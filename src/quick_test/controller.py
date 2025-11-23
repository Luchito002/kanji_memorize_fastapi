from fastapi import APIRouter, HTTPException


from . import models, service
from src.database.core import DbSession
from src.api_response import APIResponse
from src.auth.service import CurrentUser

router = APIRouter(prefix="/quicktest", tags=["quicktest"])

# Crear nueva tarjeta
@router.post("/get-quick-test-questions", response_model=APIResponse[models.GetQuickTestResponse])
def get_quick_test_questions(current_user: CurrentUser, db: DbSession, request: models.GetQuickTestRequest):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    questions = service.get_quick_test_questions(db, user_id, request.create_new)
    return APIResponse(
        result=questions,
        status="success",
        message="Questions obtained successfully"
    )

@router.post("/submit-quick-test-answer", response_model=APIResponse[models.SubmitQuickTestAnswerResponse])
def submit_quick_test_answer(
    request: models.SubmitQuickTestAnswerRequest,
    current_user: CurrentUser,
    db: DbSession
):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    result = service.submit_quick_test_answer(
        db,
        user_id,
        request.test_id,
        request.question_id,
        request.chosen_option
    )

    return APIResponse(
        result=result,
        status="success",
        message="Answer submitted successfully"
    )
