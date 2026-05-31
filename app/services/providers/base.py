from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.generation import GenerationJobCreateRequest, ModelCapability


@dataclass(frozen=True)
class ProviderImage:
    url: str
    tags: list[str]


@dataclass(frozen=True)
class ProviderResult:
    images: list[ProviderImage]


class ImageProvider(ABC):
    def __init__(self, capability: ModelCapability) -> None:
        self.capability = capability

    @abstractmethod
    async def generate_images(self, request: GenerationJobCreateRequest) -> ProviderResult:
        raise NotImplementedError
