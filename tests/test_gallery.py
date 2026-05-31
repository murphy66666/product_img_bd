from fastapi.testclient import TestClient

from app.main import app
from app.schemas.gallery import GeneratedImage


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "admin", "password": "admin123"},
    )
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_gallery_returns_pagination_meta(monkeypatch) -> None:
    async def list_gallery(
        user_id: str,
        category: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GeneratedImage], int]:
        assert user_id == "admin"
        assert category is None
        assert page == 1
        assert page_size == 20
        return [
            GeneratedImage(
                id="g-persisted",
                url="https://example.com/generated.jpg",
                originalUrl="https://example.com/source.jpg",
                prompt="Premium product image",
                model="gpt-images-2",
                resolution="2k",
                aspectRatio="1:1",
                category="main",
                createdAt="2026-05-31T10:00:00",
                tags=["test"],
            )
        ], 1

    monkeypatch.setattr("app.services.gallery_service.repository.list_gallery", list_gallery)

    client = TestClient(app)
    response = client.get("/api/v1/gallery", headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["pagination"] == {"page": 1, "pageSize": 20, "total": 1}
    assert body["data"]["images"][0]["id"] == "g-persisted"
