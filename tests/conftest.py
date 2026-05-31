import pytest

from app.services.auth_service import AuthService


ADMIN_USER = {
    "id": "admin",
    "phone": "admin",
    "name": "admin",
    "avatar": "",
    "balance": 0,
    "role": "admin",
    "password_hash": "test-admin-password-hash",
}


@pytest.fixture(autouse=True)
def admin_auth_user(monkeypatch: pytest.MonkeyPatch) -> None:
    async def find_database_user(self: AuthService, login_name: str) -> dict[str, object] | None:
        if login_name == "admin":
            return ADMIN_USER
        return None

    async def find_database_user_by_id(self: AuthService, user_id: str) -> dict[str, object] | None:
        if user_id == "admin":
            return ADMIN_USER
        return None

    def verify_password(self: AuthService, plain_password: str, password_hash: str | None) -> bool:
        return plain_password == "admin123" and password_hash == ADMIN_USER["password_hash"]

    monkeypatch.setattr(AuthService, "_find_database_user", find_database_user)
    monkeypatch.setattr(AuthService, "_find_database_user_by_id", find_database_user_by_id)
    monkeypatch.setattr(AuthService, "_verify_password", verify_password)
