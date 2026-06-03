from datetime import UTC, datetime, timedelta

from redis.exceptions import RedisError

from app.cache.redis import get_redis_client
from app.core.config import get_settings

_LOCAL_TOKENS: dict[str, tuple[str, datetime]] = {}
_REVOKED_TOKENS: set[str] = set()


class TokenStore:
    async def save(self, token: str, user_id: str) -> None:
        settings = get_settings()
        _REVOKED_TOKENS.discard(token)
        await self._with_redis("setex", self._key(token), settings.token_idle_ttl_seconds, user_id)
        _LOCAL_TOKENS[token] = (
            user_id,
            datetime.now(UTC) + timedelta(seconds=settings.token_idle_ttl_seconds),
        )

    async def validate_and_refresh(self, token: str, user_id: str) -> bool:
        if token in _REVOKED_TOKENS:
            return False
        settings = get_settings()
        cached_user_id = await self._with_redis("get", self._key(token))
        if cached_user_id is not None:
            if cached_user_id != user_id:
                return False
            await self._with_redis("expire", self._key(token), settings.token_idle_ttl_seconds)
            return True

        local_user_id, expires_at = _LOCAL_TOKENS.get(token, (None, datetime.min.replace(tzinfo=UTC)))
        if local_user_id != user_id or expires_at <= datetime.now(UTC):
            _LOCAL_TOKENS.pop(token, None)
            return False
        _LOCAL_TOKENS[token] = (
            user_id,
            datetime.now(UTC) + timedelta(seconds=settings.token_idle_ttl_seconds),
        )
        return True

    async def delete(self, token: str) -> None:
        _REVOKED_TOKENS.add(token)
        await self._with_redis("delete", self._key(token))
        _LOCAL_TOKENS.pop(token, None)

    def is_revoked(self, token: str) -> bool:
        return token in _REVOKED_TOKENS

    async def _with_redis(self, command: str, *args: object) -> object | None:
        client = get_redis_client()
        try:
            method = getattr(client, command)
            return await method(*args)
        except (RedisError, OSError, RuntimeError, AttributeError):
            return None

    def _key(self, token: str) -> str:
        return f"auth:token:{token}"


token_store = TokenStore()
