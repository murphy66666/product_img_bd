from app.schemas.generation import GenerationJobCreateRequest, ModelCapability
from app.services.providers.base import ImageProvider, ProviderImage, ProviderResult

_PRODUCT_POOLS = {
    "cosmetic": [
        "https://images.unsplash.com/photo-1512496015851-a90fb38ba796?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=800&q=80",
    ],
    "sneaker": [
        "https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?auto=format&fit=crop&w=800&q=80",
    ],
    "digital": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1487215078519-e21cc028cb29?auto=format&fit=crop&w=800&q=80",
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?auto=format&fit=crop&w=800&q=80",
    ],
}


def _select_pool(request: GenerationJobCreateRequest) -> tuple[str, list[str]]:
    source = f"{request.prompt} {request.source_image_url}".lower()
    if any(token in source for token in ["shoe", "sneaker", "jimeng", "鞋"]):
        return "sneaker", _PRODUCT_POOLS["sneaker"]
    if any(token in source for token in ["headphone", "digital", "耳机"]):
        return "digital", _PRODUCT_POOLS["digital"]
    return "cosmetic", _PRODUCT_POOLS["cosmetic"]


class MockImageProvider(ImageProvider):
    def __init__(self, capability: ModelCapability) -> None:
        super().__init__(capability)

    async def generate_images(self, request: GenerationJobCreateRequest) -> ProviderResult:
        theme, pool = _select_pool(request)
        images = []
        for index in range(request.quantity):
            images.append(
                ProviderImage(
                    url=pool[index % len(pool)],
                    tags=[request.category, self.capability.provider, theme],
                )
            )
        return ProviderResult(images=images)
