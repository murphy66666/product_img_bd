from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.schemas.gallery import GeneratedImage
from app.schemas.generation import (
    GenerationJob,
    GenerationJobCreateRequest,
    ModelCapability,
    ProviderStatus,
)
from app.schemas.session import ChatMessage
from app.services.clock import now_text
from app.services.image_storage import get_image_storage_service
from app.services.langchain_service import LangChainService, get_langchain_service
from app.services.model_registry import get_model, list_models
from app.services.providers.factory import get_provider
from app.services.repository import repository


class GenerationService:
    def __init__(self, langchain_service: LangChainService) -> None:
        self.langchain_service = langchain_service

    def list_models(self) -> list[ModelCapability]:
        return list_models()

    def list_provider_statuses(self) -> list[ProviderStatus]:
        settings = get_settings()
        provider_config = {
            "openai": (settings.openai_base_url, settings.openai_api_key),
            "google": (settings.gemini_base_url, settings.gemini_api_key),
            "bytedance": (settings.jimeng_base_url, settings.jimeng_api_key),
            "alibaba": (
                settings.alibaba_happyhouse_base_url,
                settings.alibaba_happyhouse_api_key,
            ),
        }
        statuses: list[ProviderStatus] = []

        for capability in list_models():
            base_url, api_key = provider_config.get(capability.provider, (None, None))
            if not api_key:
                status_value = "missing_api_key"
                message = "API key is not configured; real provider requests cannot be tested."
            elif not base_url:
                status_value = "missing_base_url"
                message = "Base URL is not configured; real provider requests cannot be tested."
            elif capability.provider == "openai":
                status_value = "ready"
                message = "Credentials and base URL are configured; edit-image provider requests are enabled."
            else:
                status_value = "mock_only"
                message = "Credentials and base URL are configured, but current provider implementation is mock-only."

            statuses.append(
                ProviderStatus(
                    provider=capability.provider,
                    model=capability.model,
                    providerModelId=capability.provider_model_id,
                    displayName=capability.display_name,
                    baseUrl=base_url,
                    apiKeyConfigured=bool(api_key),
                    apiKeyPreview=_preview_secret(api_key),
                    implementation="real" if status_value == "ready" else "mock",
                    status=status_value,
                    message=message,
                )
            )

        return statuses

    async def create_job(self, user_id: str, payload: GenerationJobCreateRequest) -> GenerationJob:
        capability = self._validate_capability(payload)
        created = now_text()
        job_id = f"job-{uuid4().hex[:12]}"
        user_message = ChatMessage(
            id=f"m-{uuid4().hex[:12]}",
            sender="user",
            text=f"Generation request submitted with {payload.model} for {payload.n} image(s).",
            createdAt=created,
            type="parameters",
            payload={
                "model": payload.model,
                "aspectRatio": payload.aspect_ratio,
                "resolution": payload.resolution,
                "quantity": payload.quantity,
                "size": payload.size,
                "n": payload.n,
                "quality": payload.quality,
                "outputFormat": payload.output_format,
                "sourceImageIds": payload.source_image_ids,
                "prompt": payload.prompt,
                "uploadedImageUrl": payload.source_image_url,
            },
        )
        if payload.session_id:
            await repository.add_message(user_id, payload.session_id, user_message)

        job = GenerationJob(
            id=job_id,
            status="pending",
            provider=capability.provider,
            model=payload.model,
            category=payload.category,
            aspectRatio=payload.aspect_ratio,
            resolution=payload.resolution,
            quantity=payload.quantity,
            prompt=payload.prompt,
            sourceImageUrl=payload.source_image_url,
            sourceImageIds=payload.source_image_ids,
            size=payload.size,
            quality=payload.quality,
            n=payload.n,
            outputFormat=payload.output_format,
            stream=payload.stream,
            requestedCount=payload.n,
            returnedCount=0,
            createdAt=created,
            updatedAt=created,
            images=[],
            messages=[user_message],
        )
        await repository.save_job(user_id, job, payload.session_id)
        return job

    async def run_job(self, user_id: str, job_id: str, payload: GenerationJobCreateRequest) -> None:
        capability = self._validate_capability(payload)
        await repository.update_job_status(user_id, job_id, "running")
        try:
            prompt = self.langchain_service.build_prompt(payload)
            provider = get_provider(payload.model)
            provider_result = await provider.generate_images(payload)
            storage = get_image_storage_service()
            created = now_text()
            images: list[GeneratedImage] = []

            for index, image in enumerate(provider_result.images):
                stored = None
                if provider_result.endpoint == "/images/edits" and (image.url or image.b64_json):
                    stored = await storage.save_provider_image(
                        user_id=user_id,
                        output_format=payload.output_format,
                        remote_url=image.url,
                        b64_json=image.b64_json,
                    )
                image_url = stored.public_url if stored else image.url
                if not image_url:
                    continue
                images.append(
                    GeneratedImage(
                        id=f"g-{uuid4().hex[:12]}",
                        url=image_url,
                        remoteUrl=stored.remote_url if stored else image.url,
                        localPath=stored.local_path if stored else None,
                        publicUrl=stored.public_url if stored else None,
                        mimeType=stored.mime_type if stored else None,
                        fileSize=stored.file_size if stored else None,
                        checksumSha256=stored.checksum_sha256 if stored else None,
                        originalUrl=payload.source_image_url,
                        prompt=payload.prompt,
                        model=payload.model,
                        resolution=payload.resolution,
                        aspectRatio=payload.aspect_ratio,
                        category=payload.category,
                        createdAt=created,
                        tags=[
                            *image.tags,
                            f"provider_index:{index}",
                            f"requested:{payload.n}",
                            f"returned:{len(provider_result.images)}",
                        ],
                    )
                )

            if payload.session_id:
                assistant_message = ChatMessage(
                    id=f"m-{uuid4().hex[:12]}",
                    sender="assistant",
                    text="Generation completed and images were saved to the gallery.",
                    createdAt=created,
                    type="grid_result",
                    payload={"images": [image.url for image in images], "promptPreview": prompt[:160]},
                )
                await repository.add_message(user_id, payload.session_id, assistant_message)

            await repository.add_gallery_images(
                user_id,
                job_id,
                payload.session_id,
                capability.provider,
                images,
                source_image_ids=payload.source_image_ids,
            )
            await repository.update_job_result(
                user_id=user_id,
                job_id=job_id,
                status="succeeded" if images else "failed",
                provider_result=provider_result,
                requested_count=payload.n,
                returned_count=len(images),
                source_image_ids=payload.source_image_ids,
                size=payload.size,
                quality=payload.quality,
                output_format=payload.output_format,
                stream=payload.stream,
            )
        except Exception as exc:
            await repository.update_job_status(
                user_id,
                job_id,
                "failed",
                error_code=exc.__class__.__name__,
                error_message=_client_safe_error(exc),
            )

    async def get_job(self, user_id: str, job_id: str) -> GenerationJob:
        job = await repository.get_job(user_id, job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation job not found")
        return job

    def _validate_capability(self, payload: GenerationJobCreateRequest) -> ModelCapability:
        capability = get_model(payload.model)
        if capability is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported model")
        if payload.aspect_ratio not in capability.supported_aspect_ratios:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported aspect ratio")
        if payload.resolution not in capability.supported_resolutions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported resolution")
        if payload.quantity > capability.max_quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity exceeds model limit")
        if payload.n > capability.max_quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Output count exceeds model limit")
        if payload.model == "gpt-image-2" and payload.size not in capability.supported_resolutions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported size")
        if capability.provider == "openai" and not payload.source_image_ids and not payload.source_image_url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one source image is required")
        if payload.source_image_url and not capability.supports_image_input:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Model does not support image input")
        return capability


def get_generation_service() -> GenerationService:
    return GenerationService(get_langchain_service())


def _preview_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def _client_safe_error(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return "Generation failed"
    return message[:500]
