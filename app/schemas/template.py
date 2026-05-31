from typing import Literal

from pydantic import Field

from app.schemas.common import CamelModel

SmartTemplateType = Literal[1, 2]


class SmartTemplate(CamelModel):
    id: str
    name: str
    image_url: str = Field(alias="imageUrl")
    prompt: str
    model: str
    aspect_ratio: str = Field(alias="aspectRatio")
    resolution: str
    quantity: int
    type: SmartTemplateType


class SmartTemplateListData(CamelModel):
    templates: list[SmartTemplate]
