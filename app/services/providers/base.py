from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.generation import GenerationJobCreateRequest, ModelCapability


@dataclass(frozen=True)
class ProviderImage:
    tags: list[str]
    url: str | None = None
    b64_json: str | None = None
    response_item: dict[str, object] | None = None


@dataclass(frozen=True)
class ProviderResult:
    images: list[ProviderImage]
    endpoint: str | None = None
    request_payload: dict[str, object] | None = None
    response_payload: dict[str, object] | None = None
    provider_created: int | None = None
    total_tokens: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    input_text_tokens: int | None = None
    input_image_tokens: int | None = None


class ImageProvider(ABC):
    def __init__(self, capability: ModelCapability) -> None:
        self.capability = capability

    @abstractmethod
    async def generate_images(self, request: GenerationJobCreateRequest) -> ProviderResult:
        raise NotImplementedError
