from typing import Literal

from pydantic import Field

from app.schemas.common import CamelModel, PaginationMeta

Category = Literal["main", "detail"]


class GeneratedImage(CamelModel):
    id: str
    url: str
    remote_url: str | None = Field(default=None, alias="remoteUrl")
    local_path: str | None = Field(default=None, alias="localPath")
    public_url: str | None = Field(default=None, alias="publicUrl")
    mime_type: str | None = Field(default=None, alias="mimeType")
    file_size: int | None = Field(default=None, alias="fileSize")
    checksum_sha256: str | None = Field(default=None, alias="checksumSha256")
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
