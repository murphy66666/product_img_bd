from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "admin", "password": "admin123"},
    )
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_image_saves_to_storage() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/uploads/images",
        headers=auth_headers(client),
        files={"file": ("sample.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )

    assert response.status_code == 200
    image = response.json()["data"]["image"]
    assert image["url"].startswith("/storage/app/pic/")
    stored = Path("storage/app/pic") / image["filename"]
    assert stored.exists()
    stored.unlink()
