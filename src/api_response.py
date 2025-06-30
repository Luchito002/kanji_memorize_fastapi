from typing import Optional, Generic, TypeVar
from pydantic.generics import GenericModel

T = TypeVar("T")

class APIResponse(GenericModel, Generic[T]):
    status: str = "success"
    message: Optional[str] = None
    result: Optional[T] = None
