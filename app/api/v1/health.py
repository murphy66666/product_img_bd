from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.mysql import check_mysql_connection
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/health", tags=["health"])


class HealthData(BaseModel):
    status: str
    app_name: str
    environment: str


class DatabaseHealthData(BaseModel):
    status: str
    connected: bool
    database: str | None = None


@router.get("", response_model=ApiResponse[HealthData])
async def health() -> ApiResponse[HealthData]:
    settings = get_settings()
    return ApiResponse(
        success=True,
        data=HealthData(status="ok", app_name=settings.app_name, environment=settings.app_env),
        message="ok",
    )


@router.get("/db", response_model=ApiResponse[DatabaseHealthData])
async def database_health(response: Response) -> ApiResponse[DatabaseHealthData]:
    try:
        result = await check_mysql_connection()
    except SQLAlchemyError as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ApiResponse(
            success=False,
            data=DatabaseHealthData(status="error", connected=False),
            message=f"database connection failed: {exc.__class__.__name__}",
        )

    connected = bool(result["connected"])
    if not connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ApiResponse(
        success=connected,
        data=DatabaseHealthData(
            status="ok" if connected else "error",
            connected=connected,
            database=result["database"] if isinstance(result["database"], str) else None,
        ),
        message="ok" if connected else "database connection failed",
    )
