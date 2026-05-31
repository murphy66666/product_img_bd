from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/health", tags=["health"])


class HealthData(BaseModel):
    status: str
    app_name: str
    environment: str


@router.get("", response_model=ApiResponse[HealthData])
async def health() -> ApiResponse[HealthData]:
    settings = get_settings()
    return ApiResponse(
        success=True,
        data=HealthData(status="ok", app_name=settings.app_name, environment=settings.app_env),
        message="ok",
    )
