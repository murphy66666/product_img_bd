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
    assert {"gpt-image-2", "gemini-banana", "jimeng", "happyhouse"}.issubset(models)


def test_list_provider_statuses_masks_keys() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/generation/providers/status", headers=auth_headers(client))
    assert response.status_code == 200
    body = response.json()
    providers = body["data"]["providers"]

    assert body["success"] is True
    assert {item["model"] for item in providers} == {
        "gpt-image-2",
        "gemini-banana",
        "jimeng",
        "happyhouse",
    }
    assert all("apiKeyConfigured" in item for item in providers)
    assert all("apiKeyPreview" in item for item in providers)
    assert all(item["implementation"] in {"mock", "real"} for item in providers)


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


def test_create_openai_edit_generation_job_normalizes_payload() -> None:
    client = TestClient(app)
    payload = {
        "model": "gpt-image-2",
        "category": "detail",
        "prompt": "Create three ecommerce detail images from the uploaded references",
        "sourceImageIds": ["sample.png"],
        "size": "1024x1024",
        "quality": "high",
        "n": 3,
        "outputFormat": "png\n",
        "stream": False,
    }
    response = client.post(
        "/api/v1/generation/jobs",
        json=payload,
        headers=auth_headers(client),
    )
    assert response.status_code == 200
    job = response.json()["data"]["job"]
    assert job["model"] == "gpt-image-2"
    assert job["size"] == "1024x1024"
    assert job["quantity"] == 3
    assert job["n"] == 3
    assert job["outputFormat"] == "png"
    assert job["sourceImageIds"] == ["sample.png"]
