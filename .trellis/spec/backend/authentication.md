# Authentication and Authorization

The frontend currently has only local demo login. The backend must not trust that localStorage state once real APIs exist.

## Expected Backend Pattern

Use FastAPI dependencies for authenticated routes:

```python
from fastapi import Depends, HTTPException, status

async def get_current_user() -> UserContext:
    ...
```

Protected route functions should depend on `get_current_user()` and use the returned user id for database queries.

## Session or Token Storage

Acceptable approaches:

- JWT access token plus refresh token, with secrets in environment variables.
- Server-side session id stored in Redis.
- OAuth or enterprise login later, if product requirements demand it.

Do not store secrets in frontend code or repository files.

## Scenario: Development JWT Session Recovery

### 1. Scope / Trigger
- Trigger: Protected API polling can happen after long-running generation jobs. In development, Redis may be unavailable and Uvicorn reloads can clear the process-local token store while the JWT is still valid.

### 2. Signatures
- Dependency: `get_current_user(token: str, service: AuthService) -> UserProfile`
- Token store methods: `validate_and_refresh(token, user_id)`, `save(token, user_id)`, `is_revoked(token)`
- Environment gate: `APP_ENV != "production"` permits recovery; production requires the server-side token store.

### 3. Contracts
- JWT signature and `exp` must validate before any fallback recovery.
- If `token_store.validate_and_refresh()` fails in non-production and `token_store.is_revoked(token)` is false, re-save the token and continue.
- If the token was revoked through logout in the current process, recovery must not happen.
- In production, missing Redis/session-store records must remain `401 Invalid or expired authentication token`.

### 4. Validation & Error Matrix
- Valid JWT + missing local token store + development -> restore token store and return current user.
- Valid JWT + revoked token -> `401 Invalid or expired authentication token`.
- Valid JWT + missing token store + production -> `401 Invalid or expired authentication token`.
- Invalid JWT signature or expired JWT -> `401 Invalid authentication token`.

### 5. Good/Base/Bad Cases
- Good: A generation job finishes after a local reload, and `GET /api/v1/generation/jobs/{job_id}` can still return the job while the JWT is valid.
- Base: User logs out and the same token is rejected in the same process.
- Bad: The frontend sees generated images from the provider but cannot poll the saved job because only the process-local token cache was lost.

### 6. Tests Required
- Route test clearing `_LOCAL_TOKENS` after login must still allow `/api/v1/auth/me` in development and repopulate the local token store.
- Logout invalidation test must verify revoked tokens still return `401`.

### 7. Wrong vs Correct

#### Wrong
```python
if not await token_store.validate_and_refresh(token, user_id):
    raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
```

#### Correct
```python
if not await token_store.validate_and_refresh(token, user_id):
    if settings.app_env != "production" and not token_store.is_revoked(token):
        await token_store.save(token, user_id)
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
```

## Password Handling

- Never store plain-text passwords.
- Use a proven password hashing library such as `passlib` with bcrypt or argon2.
- Rate-limit login attempts using Redis or equivalent.
- Return generic login errors to avoid account enumeration.

## Authorization

Model roles explicitly if needed:

- normal user
- VIP/member user
- admin/operator

Check ownership on generation jobs, gallery images, uploaded files, and account balance operations. Do not accept `user_id` from request bodies for protected user-scoped operations; derive it from auth context.

## Frontend Transition

When backend auth is added, update the Vue frontend so `authStore.login()` calls the backend instead of writing a demo user directly. Keep the public JSON response stable and document token/session fields.

## Scenario: Database-Backed Login Without Demo Fallback

### 1. Scope / Trigger
- Trigger: Removing demo users from production data requires removing the backend path that auto-creates or accepts `u-demo`.

### 2. Signatures
- API: `POST /api/v1/auth/login`
- Lookup: `users.phone` or `users.name`
- Token subject: existing `users.id`

### 3. Contracts
- Login succeeds only when a database user exists and password hash verification passes.
- The backend must not auto-create users during login.
- `GET /api/v1/auth/me` must resolve the token subject from `users.id`; missing users return `401`.

### 4. Validation & Error Matrix
- Unknown login name -> `401 Invalid credentials`.
- Wrong password -> `401 Invalid credentials`.
- Token subject missing from `users` -> `401 Invalid authentication token`.

### 5. Good/Base/Bad Cases
- Good: `admin` exists in `users`, password verifies, token subject is `admin`.
- Base: MySQL is unavailable, login fails closed instead of creating a fallback user.
- Bad: phone `13800138000` plus password `123456` creates or authenticates `u-demo`.

### 6. Tests Required
- Route test that demo credentials are rejected when no database user exists.
- Route test that a monkeypatched database `admin` user can log in and call `/me`.

### 7. Wrong vs Correct

#### Wrong
```python
if payload.password == "123456":
    await ensure_demo_user(payload.phone)
```

#### Correct
```python
if user is None or not verify_password(payload.password, user["password_hash"]):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```
