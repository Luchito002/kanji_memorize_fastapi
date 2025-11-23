from typing import List
from pydantic import BaseModel

class UserPreferencesResponse(BaseModel) :
    question_id: str
    selected_options: List[str]
