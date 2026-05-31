from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_user
from app.schemas.auth import UserProfile
from app.schemas.common import ApiResponse
from app.schemas.upload import UploadData
from app.services.upload_service import UploadService, get_upload_service

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/images", response_model=ApiResponse[UploadData])
async def upload_image(
    file: UploadFile = File(...),
    _current_user: UserProfile = Depends(get_current_user),
    service: UploadService = Depends(get_upload_service),
) -> ApiResponse[UploadData]:
    image = await service.save_image(file)
    return ApiResponse(success=True, data=UploadData(image=image), message="ok")
