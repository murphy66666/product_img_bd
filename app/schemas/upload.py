from pydantic import Field

from app.schemas.common import CamelModel


class UploadedImage(CamelModel):
    url: str
    filename: str
    content_type: str = Field(alias="contentType")
    size: int


class UploadData(CamelModel):
    image: UploadedImage
