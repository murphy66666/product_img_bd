from fastapi.testclient import TestClient

from app.main import app
from app.schemas.session import ChatMessage, ChatSession, SessionConfig
from app.services.clock import now_text
from app.services.repository import _json, _tutorial_messages


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "admin", "password": "admin123"},
    )
    token = response.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def persisted_session(category: str = "main") -> ChatSession:
    created_at = now_text()
    return ChatSession(
        id="s-persisted",
        title="New main image session",
        category=category,
        createdAt=created_at,
        config=SessionConfig(aspectRatio="1:1"),
        messages=[
            ChatMessage(
                id="m-persisted",
                sender="assistant",
                text="Welcome to main image mode. Upload a product image and write a prompt to start.",
                createdAt=created_at,
                type="message",
            )
        ],
    )


def test_json_helper_serializes_pydantic_models() -> None:
    assert _json(SessionConfig(aspectRatio="1:1")) == (
        '{"model":"gemini-banana","aspectRatio":"1:1","resolution":"2k",'
        '"quantity":1,"prompt":"","uploadedImageUrl":""}'
    )


def test_tutorial_messages_include_generation_dialogue_example() -> None:
    messages = _tutorial_messages("main", "2026-05-31T10:00:00")

    assert [message.sender for message in messages] == ["assistant", "user", "assistant"]
    assert all(message.payload and message.payload["tutorial"] is True for message in messages)
    assert "主图生成教程" in messages[0].text
    assert "生成一张电商主图" in messages[1].text
    assert "1:1" in messages[2].text


def test_create_session_returns_database_session(monkeypatch) -> None:
    async def create_session(user_id: str, category: str, title: str | None = None) -> ChatSession:
        assert user_id == "admin"
        assert category == "main"
        assert title is None
        return persisted_session(category)

    monkeypatch.setattr("app.services.session_service.repository.create_session", create_session)

    client = TestClient(app)
    response = client.post(
        "/api/v1/sessions",
        json={"category": "main"},
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    body = response.json()
    session = body["data"]
    assert body["success"] is True
    assert session["id"] == "s-persisted"
    assert session["messages"][0]["sender"] == "assistant"


def test_list_sessions_returns_pagination_meta(monkeypatch) -> None:
    async def list_sessions(user_id: str, page: int, page_size: int) -> tuple[list[ChatSession], int]:
        assert user_id == "admin"
        assert page == 1
        assert page_size == 20
        return [persisted_session()], 1

    monkeypatch.setattr("app.services.session_service.repository.list_sessions", list_sessions)

    client = TestClient(app)
    response = client.get("/api/v1/sessions", headers=auth_headers(client))

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["pagination"] == {"page": 1, "pageSize": 20, "total": 1}
    assert body["data"]["sessions"][0]["id"] == "s-persisted"


def test_create_session_reports_database_unavailable(monkeypatch) -> None:
    async def create_session(user_id: str, category: str, title: str | None = None) -> ChatSession:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr("app.services.session_service.repository.create_session", create_session)

    client = TestClient(app)
    response = client.post(
        "/api/v1/sessions",
        json={"category": "main"},
        headers=auth_headers(client),
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Session database is unavailable"
