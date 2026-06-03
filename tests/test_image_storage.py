from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.image_storage import _download_image, get_image_storage_service

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x00IEND\xaeB`\x82"


class FakeHeaders:
    def __init__(self, content_type: str, content_length: int | None = None) -> None:
        self._content_type = content_type
        self._content_length = content_length

    def get_content_type(self) -> str:
        return self._content_type

    def get(self, key: str) -> str | None:
        if key == "Content-Length" and self._content_length is not None:
            return str(self._content_length)
        return None


class FakeResponse:
    def __init__(self, content: bytes, content_type: str, content_length: int | None = None) -> None:
        self._content = content
        self.headers = FakeHeaders(content_type, content_length)

    def read(self, size: int) -> bytes:
        return self._content[:size]

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_download_image_rejects_short_content_length(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.image_storage.urlopen",
        lambda *args, **kwargs: FakeResponse(PNG_BYTES, "image/png", len(PNG_BYTES) + 10),
    )

    with pytest.raises(ValueError, match="download was incomplete"):
        _download_image("https://oss.example.test/image.png")


def test_download_image_rejects_png_without_iend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.services.image_storage.urlopen",
        lambda *args, **kwargs: FakeResponse(b"\x89PNG\r\n\x1a\npartial", "image/png"),
    )

    with pytest.raises(ValueError, match="PNG image download was incomplete"):
        _download_image("https://oss.example.test/image.png")


@pytest.mark.asyncio
async def test_save_provider_image_persists_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage_root = Path("storage") / "test_image_storage" / uuid4().hex
    monkeypatch.setattr(
        "app.services.image_storage._download_image",
        lambda url: (PNG_BYTES, "image/png"),
    )
    monkeypatch.setattr(
        "app.services.image_storage.get_settings",
        lambda: SimpleNamespace(generated_image_storage_dir=str(storage_root), provider_timeout_seconds=1),
    )

    stored = await get_image_storage_service().save_provider_image(
        user_id="u-admin",
        output_format="png",
        remote_url="https://oss.example.test/image.png",
    )

    assert stored.mime_type == "image/png"
    assert stored.file_size == len(PNG_BYTES)
    assert len(stored.checksum_sha256) == 64
    assert (storage_root / stored.storage_date / stored.file_name).exists()
