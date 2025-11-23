from uuid import UUID
from sqlalchemy.orm import Session

from src.entities.user_preferences import UserPreferences
from src.entities.user_stories import UserStories

from .models import UserGenerateStoryRequest, UserGenerateStoryResponse, UserGetStoryRequest, UserGetStoryResponse
import logging
import requests
import json
import random
import os

from src.exceptions import UserSettingsNotFound

def get_random_option(options: list[str]) -> str | None:
    return random.choice(options) if options else None

def generate_story(story: UserGenerateStoryRequest, db: Session, user_id: UUID) -> UserGenerateStoryResponse:
    user_settings = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if not user_settings:
        logging.warning(f"User without preferences: {user_id}")
        raise UserSettingsNotFound()

    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).all()

    topic_options = next((p.selected_options for p in prefs if p.question_id == "1"), [])
    situation_options = next((p.selected_options for p in prefs if p.question_id == "3"), [])
    gender_options = next((p.selected_options for p in prefs if p.question_id == "4"), [])

    topic = get_random_option(topic_options)
    situation = get_random_option(situation_options)
    gender = get_random_option(gender_options)

    MODEL_API_TOKEN = os.getenv("MODEL_API_TOKEN")
    radicals_text = ', '.join([f"{r.char} ({r.meaning})" for r in story.radicals]) if story.radicals else "desconocidos"
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {MODEL_API_TOKEN}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                        Crea una historia mnemotécnica corta, creativa y fácil de recordar para ayudar a memorizar el kanji {story.kanji_char}, que está formado por los componentes {radicals_text}.
                        Adáptala al estilo del método Heisig: debe ser una historia visual y muy concreta, no una explicación lógica.
                        Integra elementos de {topic}, {situation} y {gender}, ya que al usuario le gustan esos temas.
                        Debes resaltar el radical e inmediatamente despues del radical poner su caracter.
                        No debes utilizar ni un solo icono.
                        No debes utilizar otro kanji o radicales que no sean correspondientes al kanji {story.kanji_char}
                        Y como respuesta solo pasa la historia. NO pases absolutamente nada mas que no sea la historia.
                    """
                }
            ]
        })
    )

    print(f"""
                        Crea una historia mnemotécnica corta, creativa y fácil de recordar para ayudar a memorizar el kanji {story.kanji_char}, que está formado por los componentes {radicals_text}.
                        Adáptala al estilo del método Heisig: debe ser una historia visual y muy concreta, no una explicación lógica.
                        Integra elementos de {topic}, {situation} y {gender}, ya que al usuario le gustan esos temas.
                        Debes resaltar el radical e inmediatamente despues del radical poner su caracter.
                        No debes utilizar ni un solo icono.
                        No debes utilizar otro kanji o radicales que no sean correspondientes al kanji {story.kanji_char}
                        Y como respuesta solo pasa la historia. NO pases absolutamente nada mas que no sea la historia.
                    """)

    if response.status_code != 200:
        logging.error(f"OpenRouter error {response.status_code}: {response.text}")
        raise Exception("Error generando historia")

    data = response.json()
    generated_story = data["choices"][0]["message"]["content"]

    if generated_story:
        new_story = UserStories(
            user_id=user_id,
            kanji_char=story.kanji_char,
            story=generated_story
        )
        db.add(new_story)
        db.commit()
        db.refresh(new_story)

    return UserGenerateStoryResponse(
        story = generated_story
    )

def get_user_story(kanji_char: UserGetStoryRequest, db: Session, user_id: UUID) -> UserGetStoryResponse:
    user_story = db.query(UserStories).filter(
        UserStories.user_id == user_id,
        UserStories.kanji_char == kanji_char.kanji_char
    ).first()

    if not user_story:
        logging.warning(f"User story not found for user: {user_id} and kanji: {kanji_char.kanji_char}")
        raise Exception("No se encontro la historia")

    return UserGetStoryResponse(
        story=user_story.story
    )
