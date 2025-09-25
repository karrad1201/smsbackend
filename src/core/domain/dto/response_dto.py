from pydantic import BaseModel
from typing import Optional, Any, List

class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    code: Optional[int] = None