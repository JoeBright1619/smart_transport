from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class Meta(BaseModel):
    total: int
    page: int
    pageSize: int


class APIResponse(BaseModel, Generic[T]):
    data: Optional[T] = None
    meta: Optional[Meta] = None
    error: Optional[ErrorDetail] = None


class PaginatedResponse(APIResponse[List[T]], Generic[T]):
    pass


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20
