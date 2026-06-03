import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.schemas.upload import UploadedImage

STORAGE_ROOT = Path("storage/app/pic")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class UploadService:
    async def save_image(self, file: UploadFile) -> UploadedImage:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only jpeg, png, webp, or gif images are allowed",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is too large")

        await asyncio.to_thread(STORAGE_ROOT.mkdir, parents=True, exist_ok=True)
        filename = f"{uuid4().hex}{ALLOWED_IMAGE_TYPES[file.content_type]}"
        target = STORAGE_ROOT / filename
        await asyncio.to_thread(target.write_bytes, content)

        return UploadedImage(
            id=filename,
            url=f"/storage/app/pic/{filename}",
            filename=filename,
            contentType=file.content_type,
            size=len(content),
        )

    def resolve_image_path(self, image_id: str) -> Path | None:
        filename = Path(image_id).name
        if filename != image_id:
            return None
        target = STORAGE_ROOT / filename
        if not target.is_file():
            return None
        return target


def get_upload_service() -> UploadService:
    return UploadService()
