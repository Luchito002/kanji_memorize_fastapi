from fastapi import APIRouter, HTTPException
from src.api_response import APIResponse
from src.database.core import DbSession
from . import models, service
from ..auth.service import CurrentUser

router = APIRouter(
    prefix="/usersstories",
    tags=["usersstories"]
)

@router.post("/generate-story", response_model=APIResponse)
def put_edit_settings(current_user: CurrentUser, db:DbSession, story: models.UserGenerateStoryRequest):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    try:
        generated_story = service.generate_story(story, db, user_id)
        return APIResponse (
            result=generated_story,
            status="success",
            message="Story generated successfully"
        )
    except Exception as e:
        print(f"Error generating story: {e}")
        return APIResponse(
            result = None,
            status = "error",
            message= "Story not generated"
        )


@router.post("/get-user-story", response_model=APIResponse)
def get_user_story(current_user: CurrentUser, db:DbSession, kanji_char: models.UserGetStoryRequest):
    user_id = current_user.get_uuid()
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    try:
        generated_story = service.get_user_story(kanji_char, db, user_id)
        return APIResponse (
            result=generated_story,
            status="success",
            message="Story found"
        )
    except Exception as e:
        print(f"Error generating story: {e}")
        return APIResponse(
            result = None,
            status = "error",
            message= "Story not generated"
        )
