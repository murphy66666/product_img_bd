from fastapi.testclient import TestClient

from app.main import app
from app.schemas.template import SmartTemplate


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "admin", "password": "admin123"},
    )
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_templates_filters_by_type(monkeypatch) -> None:
    async def list_templates(template_type: int | None = None) -> list[SmartTemplate]:
        assert template_type == 1
        return [
            SmartTemplate(
                id="tpl-main-skincare",
                name="Beauty skincare",
                imageUrl="https://example.com/skincare.jpg",
                prompt="Premium skincare serum bottle",
                model="gemini-banana",
                aspectRatio="1:1",
                resolution="2k",
                quantity=3,
                type=1,
            )
        ]

    monkeypatch.setattr("app.services.template_service.repository.list_smart_templates", list_templates)

    client = TestClient(app)
    response = client.get("/api/v1/templates?type=1", headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    templates = body["data"]["templates"]
    assert body["success"] is True
    assert templates[0]["type"] == 1
    assert templates[0]["imageUrl"] == "https://example.com/skincare.jpg"
    assert templates[0]["aspectRatio"] == "1:1"


def test_list_templates_rejects_invalid_type() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/templates?type=3", headers=auth_headers(client))

    assert response.status_code == 422
