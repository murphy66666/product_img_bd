from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import health as health_api
from app.main import app


def test_health() -> None:
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json; charset=utf-8"
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"


def test_database_health_success(monkeypatch) -> None:
    async def check_mysql_connection() -> dict[str, object]:
        return {"connected": True, "database": "product_ai"}

    monkeypatch.setattr(health_api, "check_mysql_connection", check_mysql_connection)

    response = TestClient(app).get("/api/v1/health/db")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == {"status": "ok", "connected": True, "database": "product_ai"}


def test_database_health_failure(monkeypatch) -> None:
    async def check_mysql_connection() -> dict[str, object]:
        raise SQLAlchemyError("connection failed")

    monkeypatch.setattr(health_api, "check_mysql_connection", check_mysql_connection)

    response = TestClient(app).get("/api/v1/health/db")
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["data"]["status"] == "error"
    assert body["data"]["connected"] is False
