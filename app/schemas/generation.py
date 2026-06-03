from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.schemas.common import CamelModel
from app.schemas.gallery import Category, GeneratedImage
from app.schemas.session import ChatMessage

JobStatus = Literal["pending", "running", "succeeded", "failed", "partial_failed"]
ImageQuality = Literal["low", "medium", "high", "auto"]
ImageOutputFormat = Literal["png", "jpeg", "webp"]


class ModelCapability(CamelModel):
    provider: str
    model: str
    provider_model_id: str = Field(alias="providerModelId")
    display_name: str = Field(alias="displayName")
    supported_aspect_ratios: list[str] = Field(alias="supportedAspectRatios")
    supported_resolutions: list[str] = Field(alias="supportedResolutions")
    max_quantity: int = Field(alias="maxQuantity")
    supports_image_input: bool = Field(alias="supportsImageInput")
    requires_async_polling: bool = Field(alias="requiresAsyncPolling")


class ModelListData(CamelModel):
    models: list[ModelCapability]


class ProviderStatus(CamelModel):
    provider: str
    model: str
    provider_model_id: str = Field(alias="providerModelId")
    display_name: str = Field(alias="displayName")
    base_url: str | None = Field(default=None, alias="baseUrl")
    api_key_configured: bool = Field(alias="apiKeyConfigured")
    api_key_preview: str | None = Field(default=None, alias="apiKeyPreview")
    implementation: Literal["mock", "real"] = "mock"
    status: Literal["ready", "missing_api_key", "missing_base_url", "mock_only"]
    message: str


class ProviderStatusData(CamelModel):
    providers: list[ProviderStatus]


class GenerationJobCreateRequest(CamelModel):
    model: str
    category: Category = "main"
    aspect_ratio: str = Field(default="1:1", alias="aspectRatio")
    resolution: str = "1024x1024"
    quantity: int = Field(default=1, ge=1, le=8)
    prompt: str = Field(min_length=1, max_length=32000)
    source_image_url: str = Field(default="", alias="sourceImageUrl")
    session_id: str | None = Field(default=None, alias="sessionId")
    source_image_ids: list[str] = Field(default_factory=list, alias="sourceImageIds")
    size: str = "1024x1024"
    quality: ImageQuality = "high"
    n: int = Field(default=1, ge=1, le=8)
    output_format: ImageOutputFormat = Field(default="png", alias="outputFormat")
    stream: bool = False

    @field_validator("size", mode="before")
    @classmethod
    def clean_size(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("output_format", mode="before")
    @classmethod
    def clean_output_format(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def normalize_edit_fields(self) -> "GenerationJobCreateRequest":
        self.size = self.size.strip()
        if self.n == 1 and self.quantity != 1:
            self.n = self.quantity
        else:
            self.quantity = self.n
        if self.model == "gpt-image-2":
            self.resolution = self.size
        return self


class GenerationJob(CamelModel):
    id: str
    status: JobStatus
    provider: str
    model: str
    category: Category
    aspect_ratio: str = Field(alias="aspectRatio")
    resolution: str
    quantity: int
    prompt: str
    source_image_url: str = Field(alias="sourceImageUrl")
    source_image_ids: list[str] = Field(default_factory=list, alias="sourceImageIds")
    size: str = "1024x1024"
    quality: ImageQuality = "high"
    n: int = 1
    output_format: ImageOutputFormat = Field(default="png", alias="outputFormat")
    stream: bool = False
    requested_count: int | None = Field(default=None, alias="requestedCount")
    returned_count: int | None = Field(default=None, alias="returnedCount")
    created_at: str = Field(alias="createdAt")
    updated_at: str = Field(alias="updatedAt")
    images: list[GeneratedImage] = []
    messages: list[ChatMessage] = []
    error_code: str | None = Field(default=None, alias="errorCode")
    error_message: str | None = Field(default=None, alias="errorMessage")


class GenerationJobData(CamelModel):
    job: GenerationJob
