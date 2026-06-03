import json
import mimetypes
import secrets
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.schemas.generation import GenerationJobCreateRequest, ModelCapability
from app.services.providers.base import ImageProvider, ProviderImage, ProviderResult
from app.services.upload_service import get_upload_service


class OpenAIImageEditProvider(ImageProvider):
    def __init__(self, capability: ModelCapability) -> None:
        super().__init__(capability)
        self.upload_service = get_upload_service()

    async def generate_images(self, request: GenerationJobCreateRequest) -> ProviderResult:
        settings = get_settings()
        if not settings.openai_api_key or not settings.openai_base_url:
            raise RuntimeError("OpenAI credentials are not configured")

        source_paths = self._resolve_source_paths(request.source_image_ids)
        if not source_paths:
            raise ValueError("At least one uploaded source image is required")

        endpoint = "/images/edits"
        url = _build_provider_url(settings.openai_base_url, endpoint)
        fields = {
            "model": self.capability.provider_model_id,
            "prompt": request.prompt,
            "size": request.size,
            "quality": request.quality.strip(),
            "n": str(request.n),
            "output_format": request.output_format.strip(),
            "stream": "true" if request.stream else "false",
        }
        response_payload = _post_multipart(
            url=url,
            api_key=settings.openai_api_key,
            fields=fields,
            files=[("image[]", item) for item in source_paths],
            timeout=settings.provider_timeout_seconds,
        )
        data_items = response_payload.get("data", [])
        if not isinstance(data_items, list):
            raise ValueError("Provider response data must be a list")

        images: list[ProviderImage] = []
        for item in data_items:
            if not isinstance(item, dict):
                continue
            images.append(
                ProviderImage(
                    url=item.get("url") if isinstance(item.get("url"), str) else None,
                    b64_json=item.get("b64_json") if isinstance(item.get("b64_json"), str) else None,
                    tags=["openai", "edit", request.output_format],
                    response_item=item,
                )
            )

        usage = response_payload.get("usage") if isinstance(response_payload.get("usage"), dict) else {}
        input_details = usage.get("input_tokens_details") if isinstance(usage.get("input_tokens_details"), dict) else {}
        request_payload = {
            "endpoint": endpoint,
            "contentType": "multipart/form-data",
            "model": self.capability.provider_model_id,
            "prompt": request.prompt,
            "size": request.size,
            "quality": request.quality,
            "n": request.n,
            "output_format": request.output_format,
            "stream": request.stream,
            "imageFiles": [_file_metadata(path) for path in source_paths],
        }
        return ProviderResult(
            images=images,
            endpoint=endpoint,
            request_payload=request_payload,
            response_payload=_summarize_response(response_payload, request.n),
            provider_created=response_payload.get("created") if isinstance(response_payload.get("created"), int) else None,
            total_tokens=_int_or_none(usage.get("total_tokens")),
            input_tokens=_int_or_none(usage.get("input_tokens")),
            output_tokens=_int_or_none(usage.get("output_tokens")),
            input_text_tokens=_int_or_none(input_details.get("text_tokens")),
            input_image_tokens=_int_or_none(input_details.get("image_tokens")),
        )

    def _resolve_source_paths(self, source_image_ids: list[str]) -> list[Path]:
        paths: list[Path] = []
        for image_id in source_image_ids:
            path = self.upload_service.resolve_image_path(image_id)
            if path is None:
                raise ValueError("Uploaded source image not found")
            paths.append(path)
        return paths


def _post_multipart(
    *,
    url: str,
    api_key: str,
    fields: dict[str, str],
    files: list[tuple[str, Path]],
    timeout: int,
) -> dict[str, object]:
    boundary = f"----product-image-{secrets.token_hex(16)}"
    body = bytearray()
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")
    for field_name, path in files:
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{path.name}"\r\n'
                f"Content-Type: {mime_type}\r\n\r\n"
            ).encode()
        )
        body.extend(path.read_bytes())
        body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    request = Request(
        url,
        data=bytes(body),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        message = _extract_error_message(detail)
        raise RuntimeError(f"Provider request failed with status {exc.code}: {message}") from exc
    except URLError as exc:
        raise RuntimeError("Provider request failed") from exc
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Provider response must be a JSON object")
    return payload


def _build_provider_url(base_url: str, endpoint: str) -> str:
    normalized = base_url.strip().rstrip("/")
    if normalized.endswith(endpoint):
        return normalized
    if not normalized.endswith("/v1"):
        normalized = f"{normalized}/v1"
    return f"{normalized}{endpoint}"


def _extract_error_message(detail: str) -> str:
    stripped = detail.strip()
    if not stripped:
        return "Provider request failed"
    try:
        payload: Any = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped[:500]

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, str):
        return error[:500]
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str):
            return message[:500]
    message = payload.get("message") if isinstance(payload, dict) else None
    if isinstance(message, str):
        return message[:500]
    return stripped[:500]


def _file_metadata(path: Path) -> dict[str, object]:
    return {
        "uploadId": path.name,
        "field": "image[]",
        "fileName": path.name,
        "mimeType": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "fileSize": path.stat().st_size,
    }


def _summarize_response(payload: dict[str, object], requested_count: int) -> dict[str, object]:
    data = payload.get("data") if isinstance(payload.get("data"), list) else []
    response_types = []
    summarized_data = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("url"), str):
            response_types.append("url")
            summarized_data.append({"index": index, "url": item["url"]})
        elif isinstance(item.get("b64_json"), str):
            response_types.append("b64_json")
            summarized_data.append({"index": index, "b64_json": True})
    return {
        "created": payload.get("created"),
        "requestedCount": requested_count,
        "returnedCount": len(data),
        "responseTypes": sorted(set(response_types)),
        "data": summarized_data,
        "usage": payload.get("usage"),
    }


def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) else None
