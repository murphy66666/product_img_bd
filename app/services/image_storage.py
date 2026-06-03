import asyncio
import base64
import hashlib
import mimetypes
import secrets
from dataclasses import dataclass
from datetime import datetime
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings

MAX_GENERATED_IMAGE_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True)
class StoredImage:
    url: str
    remote_url: str | None
    local_path: str
    public_url: str
    storage_date: str
    file_name: str
    file_ext: str
    mime_type: str
    file_size: int
    checksum_sha256: str


class ImageStorageService:
    async def save_provider_image(
        self,
        *,
        user_id: str,
        output_format: str,
        remote_url: str | None = None,
        b64_json: str | None = None,
    ) -> StoredImage:
        if remote_url:
            content, mime_type = await asyncio.to_thread(_download_image, remote_url)
        elif b64_json:
            content = base64.b64decode(b64_json)
            mime_type = _mime_type_for_format(output_format)
        else:
            raise ValueError("Provider image has neither url nor b64_json")

        if not content:
            raise ValueError("Provider image is empty")
        if len(content) > MAX_GENERATED_IMAGE_BYTES:
            raise ValueError("Provider image is too large")
        _validate_complete_image(content, mime_type)

        settings = get_settings()
        storage_root = Path(settings.generated_image_storage_dir)
        storage_date = datetime.now().strftime("%Y%m%d")
        folder = storage_root / storage_date
        await asyncio.to_thread(folder.mkdir, parents=True, exist_ok=True)

        file_ext = _extension_for_mime(mime_type, output_format)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        safe_user_id = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in user_id)
        file_name = f"{timestamp}_{safe_user_id}_{secrets.token_hex(4)}{file_ext}"
        target = folder / file_name
        temp = folder / f".{file_name}.tmp"

        await asyncio.to_thread(temp.write_bytes, content)
        await asyncio.to_thread(temp.replace, target)

        checksum = hashlib.sha256(content).hexdigest()
        local_path = target.as_posix()
        public_url = f"/{local_path}"
        return StoredImage(
            url=public_url,
            remote_url=remote_url,
            local_path=local_path,
            public_url=public_url,
            storage_date=storage_date,
            file_name=file_name,
            file_ext=file_ext.lstrip("."),
            mime_type=mime_type,
            file_size=len(content),
            checksum_sha256=checksum,
        )


def get_image_storage_service() -> ImageStorageService:
    return ImageStorageService()


def _download_image(url: str) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": "product-image-backend/0.1"})
    try:
        with urlopen(request, timeout=get_settings().provider_timeout_seconds) as response:
            content = response.read(MAX_GENERATED_IMAGE_BYTES + 1)
            mime_type = response.headers.get_content_type()
            expected_length = _content_length(response.headers.get("Content-Length"))
    except HTTPError as exc:
        raise ValueError(f"Failed to download provider image: HTTP {exc.code}") from exc
    except (IncompleteRead, OSError, URLError) as exc:
        raise ValueError("Failed to download provider image") from exc
    if not mime_type.startswith("image/"):
        raise ValueError("Provider URL did not return an image")
    if len(content) > MAX_GENERATED_IMAGE_BYTES:
        raise ValueError("Provider image is too large")
    if expected_length is not None and len(content) != expected_length:
        raise ValueError(
            f"Provider image download was incomplete: expected {expected_length} bytes, got {len(content)}"
        )
    _validate_complete_image(content, mime_type)
    return content, mime_type


def _content_length(value: str | None) -> int | None:
    if not value:
        return None
    try:
        length = int(value)
    except ValueError:
        return None
    return length if length >= 0 else None


def _validate_complete_image(content: bytes, mime_type: str) -> None:
    if mime_type == "image/png" or content.startswith(b"\x89PNG\r\n\x1a\n"):
        if not content.startswith(b"\x89PNG\r\n\x1a\n") or not content.endswith(
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        ):
            raise ValueError("Provider PNG image download was incomplete")
        return
    if mime_type == "image/jpeg" or content.startswith(b"\xff\xd8"):
        if not content.startswith(b"\xff\xd8") or not content.endswith(b"\xff\xd9"):
            raise ValueError("Provider JPEG image download was incomplete")
        return
    if mime_type == "image/webp" or content.startswith(b"RIFF"):
        if len(content) < 12 or content[0:4] != b"RIFF" or content[8:12] != b"WEBP":
            raise ValueError("Provider WebP image download was invalid")
        declared_size = int.from_bytes(content[4:8], "little") + 8
        if declared_size != len(content):
            raise ValueError(
                f"Provider WebP image download was incomplete: expected {declared_size} bytes, got {len(content)}"
            )
        return


def _mime_type_for_format(output_format: str) -> str:
    if output_format == "jpeg":
        return "image/jpeg"
    if output_format == "webp":
        return "image/webp"
    return "image/png"


def _extension_for_mime(mime_type: str, output_format: str) -> str:
    if output_format in {"png", "jpeg", "webp"}:
        return ".jpg" if output_format == "jpeg" else f".{output_format}"
    guessed = mimetypes.guess_extension(mime_type)
    return guessed or ".png"
