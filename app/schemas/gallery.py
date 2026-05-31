from typing import Literal

from pydantic import Field

from app.schemas.common import CamelModel, PaginationMeta

Category = Literal["main", "detail"]


class GeneratedImage(CamelModel):
    id: str
    url: str
    original_url: str = Field(alias="originalUrl")
    prompt: str
    model: str
    resolution: str
    aspect_ratio: str = Field(alias="aspectRatio")
    category: Category
    created_at: str = Field(alias="createdAt")
    tags: list[str] = []


class GalleryListData(CamelModel):
    images: list[GeneratedImage]
    pagination: PaginationMeta
