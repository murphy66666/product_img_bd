from app.schemas.generation import GenerationJobCreateRequest


class LangChainService:
    """Boundary for future LangChain prompt orchestration and provider workflows."""

    def build_prompt(self, request: GenerationJobCreateRequest) -> str:
        if request.model == "gpt-image-2":
            return (
                f"Edit {len(request.source_image_ids)} uploaded product reference image(s). "
                f"Size: {request.size}. Outputs requested: {request.n}. "
                f"Quality: {request.quality}. Prompt: {request.prompt}"
            )
        return (
            f"Generate {request.quantity} product image(s) for {request.category}. "
            f"Aspect ratio: {request.aspect_ratio}. Resolution: {request.resolution}. "
            f"Prompt: {request.prompt}"
        )


def get_langchain_service() -> LangChainService:
    return LangChainService()
