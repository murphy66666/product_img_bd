from fastapi import HTTPException, status

from app.schemas.gallery import GeneratedImage
from app.services.repository import repository


class GalleryService:
    async def list_images(
        self,
        user_id: str,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GeneratedImage], int]:
        return await repository.list_gallery(user_id, category, page, page_size)

    async def delete_image(self, user_id: str, image_id: str) -> None:
        if not await repository.delete_gallery_image(user_id, image_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")


def get_gallery_service() -> GalleryService:
    return GalleryService()
