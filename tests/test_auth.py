from fastapi.testclient import TestClient

from app.main import app
from app.services.token_store import _LOCAL_TOKENS, _REVOKED_TOKENS


def test_demo_login_is_rejected_without_database_user() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "13800138000", "password": "123456"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

def test_admin_login_uses_database_user() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "admin", "password": "admin123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["token"]
    assert body["data"]["user"]["id"] == "admin"

    token = body["data"]["token"]
    me_response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200


def test_protected_route_requires_bearer_token() -> None:
    response = TestClient(app).get("/api/v1/generation/models")

    assert response.status_code == 401


def test_logout_invalidates_bearer_token() -> None:
    client = TestClient(app)
    login_response = client.post(
        "/api/v1/auth/login",
        json={"phone": "admin", "password": "admin123"},
    )
    token = login_response.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200

    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 401


def test_development_restores_valid_jwt_when_session_cache_is_missing() -> None:
    client = TestClient(app)
    login_response = client.post(
        "/api/v1/auth/login",
        json={"phone": "admin", "password": "admin123"},
    )
    token = login_response.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    _REVOKED_TOKENS.discard(token)
    _LOCAL_TOKENS.pop(token, None)

    me_response = client.get("/api/v1/auth/me", headers=headers)

    assert me_response.status_code == 200
    assert token in _LOCAL_TOKENS


def test_cors_preflight_allows_local_dev_origins() -> None:
    response = TestClient(app).options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://192.168.1.10:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://192.168.1.10:5173"
