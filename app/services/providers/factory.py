from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services.model_registry import get_model
from app.services.providers.base import ImageProvider
from app.services.providers.mock import MockImageProvider
from app.services.providers.openai import OpenAIImageEditProvider


def get_provider(model: str) -> ImageProvider:
    capability = get_model(model)
    if capability is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported model")
    settings = get_settings()
    if capability.provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI API key is not configured")
        if not settings.openai_base_url:
            raise RuntimeError("OpenAI base URL is not configured")
        return OpenAIImageEditProvider(capability)
    return MockImageProvider(capability)
