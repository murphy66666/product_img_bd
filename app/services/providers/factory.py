from fastapi import HTTPException, status

from app.services.model_registry import get_model
from app.services.providers.base import ImageProvider
from app.services.providers.mock import MockImageProvider


def get_provider(model: str) -> ImageProvider:
    capability = get_model(model)
    if capability is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported model")
    return MockImageProvider(capability)
