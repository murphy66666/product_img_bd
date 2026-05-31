from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.schemas.auth import UserProfile
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.gallery import Category, GalleryListData
from app.services.gallery_service import GalleryService, get_gallery_service

router = APIRouter(prefix="/gallery", tags=["gallery"])


@router.get("", response_model=ApiResponse[GalleryListData])
async def list_gallery(
    category: Category | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    current_user: UserProfile = Depends(get_current_user),
    service: GalleryService = Depends(get_gallery_service),
) -> ApiResponse[GalleryListData]:
    images, total = await service.list_images(current_user.id, category, page, page_size)
    return ApiResponse(
        success=True,
        data=GalleryListData(
            images=images,
            pagination=PaginationMeta(page=page, pageSize=page_size, total=total),
        ),
        message="ok",
    )


@router.delete("/{image_id}", response_model=ApiResponse[dict[str, bool]])
async def delete_image(
    image_id: str,
    current_user: UserProfile = Depends(get_current_user),
    service: GalleryService = Depends(get_gallery_service),
) -> ApiResponse[dict[str, bool]]:
    await service.delete_image(current_user.id, image_id)
    return ApiResponse(success=True, data={"deleted": True}, message="ok")
