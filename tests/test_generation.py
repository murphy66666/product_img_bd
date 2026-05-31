from fastapi.testclient import TestClient

from app.main import app


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "admin", "password": "admin123"},
    )
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_models() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/generation/models", headers=auth_headers(client))
    assert response.status_code == 200
    body = response.json()
    models = {item["model"] for item in body["data"]["models"]}
    assert {"gpt-images-2", "gemini-banana", "jimeng", "happyhouse"}.issubset(models)


def test_list_provider_statuses_masks_keys() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/generation/providers/status", headers=auth_headers(client))
    assert response.status_code == 200
    body = response.json()
    providers = body["data"]["providers"]

    assert body["success"] is True
    assert {item["model"] for item in providers} == {
        "gpt-images-2",
        "gemini-banana",
        "jimeng",
        "happyhouse",
    }
    assert all("apiKeyConfigured" in item for item in providers)
    assert all("apiKeyPreview" in item for item in providers)
    assert all(item["implementation"] == "mock" for item in providers)


def test_create_generation_job() -> None:
    client = TestClient(app)
    payload = {
        "model": "gemini-banana",
        "category": "main",
        "aspectRatio": "1:1",
        "resolution": "2k",
        "quantity": 2,
        "prompt": "Premium skincare product photo",
        "sourceImageUrl": "https://example.com/source.jpg",
    }
    response = client.post(
        "/api/v1/generation/jobs",
        json=payload,
        headers=auth_headers(client),
    )
    assert response.status_code == 200
    body = response.json()
    job = body["data"]["job"]
    assert body["success"] is True
    assert job["status"] == "pending"
    assert job["model"] == "gemini-banana"
    assert job["images"] == []
