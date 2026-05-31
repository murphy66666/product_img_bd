from app.schemas.generation import ModelCapability

_MODEL_CAPABILITIES: dict[str, ModelCapability] = {
    "gpt-images-2": ModelCapability(
        provider="openai",
        model="gpt-images-2",
        providerModelId="gpt-images-2",
        displayName="GPT Images 2",
        supportedAspectRatios=["1:1", "3:4", "4:3", "9:16", "16:9"],
        supportedResolutions=["1k", "2k", "3k", "4k"],
        maxQuantity=4,
        supportsImageInput=True,
        requiresAsyncPolling=False,
    ),
    "gemini-banana": ModelCapability(
        provider="google",
        model="gemini-banana",
        providerModelId="gemini-banana",
        displayName="Gemini Banana",
        supportedAspectRatios=["1:1", "3:4", "4:3", "9:16", "16:9", "3:2", "2:3"],
        supportedResolutions=["1k", "2k", "3k", "4k"],
        maxQuantity=3,
        supportsImageInput=True,
        requiresAsyncPolling=False,
    ),
    "jimeng": ModelCapability(
        provider="bytedance",
        model="jimeng",
        providerModelId="jimeng-image",
        displayName="ByteDance Jimeng",
        supportedAspectRatios=["1:1", "3:4", "4:3", "9:16", "16:9", "4:5"],
        supportedResolutions=["1k", "2k", "4k"],
        maxQuantity=6,
        supportsImageInput=True,
        requiresAsyncPolling=True,
    ),
    "happyhouse": ModelCapability(
        provider="alibaba",
        model="happyhouse",
        providerModelId="happyhouse-image",
        displayName="Alibaba HappyHouse",
        supportedAspectRatios=["1:1", "3:4", "4:3", "9:16", "16:9", "21:9"],
        supportedResolutions=["1k", "2k", "3k", "4k"],
        maxQuantity=6,
        supportsImageInput=True,
        requiresAsyncPolling=True,
    ),
}


def list_models() -> list[ModelCapability]:
    return list(_MODEL_CAPABILITIES.values())


def get_model(model: str) -> ModelCapability | None:
    return _MODEL_CAPABILITIES.get(model)
