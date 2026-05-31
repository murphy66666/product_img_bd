from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.schemas.auth import UserProfile
from app.schemas.common import ApiResponse
from app.schemas.template import SmartTemplateListData, SmartTemplateType
from app.services.template_service import TemplateService, get_template_service

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=ApiResponse[SmartTemplateListData])
async def list_templates(
    template_type: int | None = Query(default=None, alias="type", ge=1, le=2),
    _current_user: UserProfile = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> ApiResponse[SmartTemplateListData]:
    templates = await service.list_templates(template_type if template_type is None else _template_type(template_type))
    return ApiResponse(success=True, data=SmartTemplateListData(templates=templates), message="ok")


def _template_type(value: int) -> SmartTemplateType:
    return 1 if value == 1 else 2
