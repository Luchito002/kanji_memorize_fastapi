from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from src.entities.daily_progress import DailyProgress
from src.quick_test.models import GetQuickTestResponse, QuickQuestionFull, QuickTestData, SubmitQuickTestAnswerResponse

from src.entities.quick_test_question import QuickTestQuestion
from src.entities.quick_test import QuickTest

import json
import random
import os

KANJI_FILE = os.path.join(os.path.dirname(__file__), "../kanjis_convertidos_normalizado.json")

def get_quick_test_questions(db: Session, user_id: UUID, create_new: bool) -> GetQuickTestResponse:
    # Obtener el último test del usuario
    last_test = (
        db.query(QuickTest)
        .filter(QuickTest.user_id == user_id)
        .order_by(QuickTest.start_time.desc())
        .first()
    )

    # 1️⃣ Si existe un test en progreso y no se pide crear uno nuevo, devolverlo
    if last_test and last_test.state != "complete" and not create_new:
        return GetQuickTestResponse(
            test=QuickTestData(
                id=last_test.id,
                state=last_test.state,
                limit=last_test.limit,
                current=last_test.current,
                correct_count=last_test.correct_count,
                wrong_count=last_test.wrong_count,
                questions=[
                    QuickQuestionFull(
                        id=q.id,
                        character=q.kanji_char,
                        meaning=q.correct_meaning,
                        options=[q.option_a, q.option_b, q.option_c, q.option_d],
                        chosen_meaning=q.chosen_meaning,
                        is_correct=q.is_correct
                    )
                    for q in last_test.questions
                ]
            )
        )

    # 2️⃣ Si no hay ningún test previo, forzar creación de uno nuevo
    if not last_test:
        create_new = True

    # 3️⃣ Si el último test está completo y no se quiere crear uno nuevo, devolverlo
    if last_test and last_test.state == "complete" and not create_new:
        return GetQuickTestResponse(
            test=QuickTestData(
                id=last_test.id,
                state=last_test.state,
                limit=last_test.limit,
                current=last_test.current,
                correct_count=last_test.correct_count,
                wrong_count=last_test.wrong_count,
                questions=[
                    QuickQuestionFull(
                        id=q.id,
                        character=q.kanji_char,
                        meaning=q.correct_meaning,
                        options=[q.option_a, q.option_b, q.option_c, q.option_d],
                        chosen_meaning=q.chosen_meaning,
                        is_correct=q.is_correct
                    )
                    for q in last_test.questions
                ]
            )
        )

    # 4️⃣ Obtener el progreso actual del usuario
    progress = (
        db.query(DailyProgress)
        .filter(DailyProgress.user_id == user_id)
        .order_by(DailyProgress.progress_date.desc())
        .first()
    )

    # Si el usuario es nuevo, crear un rango base por defecto
    if not progress:
        class DummyProgress:
            end_kanji_index = 10
        progress = DummyProgress()

    # Cargar kanji disponibles
    with open(KANJI_FILE, "r", encoding="utf-8") as f:
        kanjis = json.load(f)

    # Filtrar los kanji dentro del rango del progreso
    available_kanjis = [k for k in kanjis if k["position"] <= progress.end_kanji_index]

    if len(available_kanjis) < 10:
        raise ValueError("Not enough kanji to generate test")

    selected_kanjis = random.sample(available_kanjis, k=10)

    # Crear un nuevo test
    new_test = QuickTest(
        user_id=user_id,
        limit=10,
        current=0,
        correct_count=0,
        wrong_count=0,
        state="in_progress"
    )
    db.add(new_test)
    db.flush()

    # Crear preguntas
    questions = []
    for order, kanji in enumerate(selected_kanjis, start=1):
        wrong_kanjis = random.sample(
            [k for k in available_kanjis if k["character"] != kanji["character"]],
            k=3
        )
        options = [k["character"] for k in wrong_kanjis] + [kanji["character"]]
        random.shuffle(options)

        question = QuickTestQuestion(
            test_id=new_test.id,
            kanji_char=kanji["character"],
            correct_meaning=kanji["meaning"],
            option_a=options[0],
            option_b=options[1],
            option_c=options[2],
            option_d=options[3],
            order=order
        )
        db.add(question)
        db.flush()

        questions.append(
            QuickQuestionFull(
                id=question.id,
                character=kanji["character"],
                meaning=kanji["meaning"],
                options=options,
                chosen_meaning=None,
                is_correct=None
            )
        )

    db.commit()

    return GetQuickTestResponse(
        test=QuickTestData(
            id=new_test.id,
            state=new_test.state,
            limit=new_test.limit,
            current=new_test.current,
            correct_count=new_test.correct_count,
            wrong_count=new_test.wrong_count,
            questions=questions
        )
    )


def submit_quick_test_answer(
    db: Session,
    user_id: UUID,
    test_id: UUID,
    question_id: UUID,
    chosen_option: str,
    end_time: str | None = None  # viene como ISO string
) -> SubmitQuickTestAnswerResponse:
    # Obtener el test y la pregunta
    test = db.query(QuickTest).filter(
        QuickTest.id == test_id,
        QuickTest.user_id == user_id
    ).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    question = db.query(QuickTestQuestion).filter(
        QuickTestQuestion.id == question_id,
        QuickTestQuestion.test_id == test.id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    prev_correct = question.is_correct

    # Evaluar respuesta
    question.chosen_meaning = chosen_option
    question.is_correct = (chosen_option == question.kanji_char)

    # Actualizar contadores del test
    if prev_correct is None:
        test.current += 1
        if question.is_correct:
            test.correct_count += 1
        else:
            test.wrong_count += 1
    elif prev_correct != question.is_correct:
        if question.is_correct:
            test.correct_count += 1
            test.wrong_count -= 1
        else:
            test.correct_count -= 1
            test.wrong_count += 1

    # Determinar si es la última pregunta
    is_last_question = test.current >= test.limit

    if is_last_question:
        test.state = "complete"
        if end_time:
            # Convertir string ISO a datetime
            test.end_time = datetime.fromisoformat(end_time)
        else:
            test.end_time = datetime.now(timezone.utc)

    db.commit()
    db.refresh(test)
    db.refresh(question)

    return SubmitQuickTestAnswerResponse(
        test_id=test.id,
        question_id=question.id,
        is_correct=question.is_correct or False,
        current=test.current,
        total=test.limit,
        completed=test.state == "complete",
        correct_count=test.correct_count,
        wrong_count=test.wrong_count
    )
