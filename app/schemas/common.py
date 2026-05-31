from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str | None = None


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class PaginationMeta(CamelModel):
    page: int
    page_size: int = Field(alias="pageSize")
    total: int
