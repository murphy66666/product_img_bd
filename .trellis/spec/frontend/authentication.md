# Authentication

Authentication uses the FastAPI auth endpoints for the current demo/backend flow. It is still not a complete production auth system.

## Current Behavior

`src/components/LoginModal.vue` owns the login form:

- Phone number is required and must match `^1[3-9]\d{9}$`.
- Password is required and must be verified by the FastAPI auth endpoint.
- Optional remember-phone behavior writes `rememberedPhone` to localStorage.
- On success, it calls `authStore.login(trimmedPhone, password, rememberMe)`.

`src/stores/auth.ts` persists:

- `authToken`
- `authUser`
- `theme`

The API client keeps the bearer token in memory via `setBearerToken()`. Because page refresh clears module memory, `auth.ts` must restore `authToken` and `authUser` from browser storage at module initialization and immediately call `setBearerToken(storedToken)`.

`App.vue`/`WorkspaceView.vue` renders the workbench only when `authStore.isLoggedIn` is true; otherwise it shows the login overlay and a blurred skeleton-like background.

## Refresh Restoration Contract

- `rememberMe === true`: write `authToken` and `authUser` to localStorage.
- `rememberMe === false`: write `authToken` and `authUser` to sessionStorage.
- Always remove stale auth keys from the opposite storage when a new login succeeds.
- On startup, treat the user as logged in only when both token and user JSON parse successfully.
- On parse failure or logout, clear auth keys from both localStorage and sessionStorage and set the bearer token to `null`.

### Common Mistake: Token Only in Memory

**Symptom**: Login succeeds, but pressing F5 returns to the login overlay.

**Cause**: `setBearerToken()` stores the token in module memory, while Pinia state also resets after reload.

**Fix**: Persist safe client session fields after login and hydrate both Pinia state and the API client before protected API calls run.

## Security Constraints

- Do not treat this as production authentication.
- Do not add real secrets or API tokens to frontend source.
- Do not keep hard-coded production credentials in Vue files.
- Do not create local demo tokens or local demo users when `loginApi()` fails.
- Network errors, unavailable backend, `401`, and other auth failures must keep `authStore.isLoggedIn === false` and surface a visible login error.
- Do not rely on localStorage for authorization decisions once backend APIs are protected.

### Common Mistake: Frontend Demo Auth Fallback

**Symptom**: Backend auth rejects or is unavailable, but the user can still enter the app with a hard-coded demo password.

**Cause**: `authStore.login()` catches `loginApi()` failures and creates a local token/user object.

**Fix**: Let `loginApi()` errors propagate to `LoginModal.vue`; only set `isLoggedIn`, `user`, bearer token, and persisted auth storage after the backend returns a successful login response.

**Prevention**: If offline demo login is ever required again, gate it behind an explicit development-only configuration flag and make the disabled production path the default.

## If Backend Auth Is Added

Introduce an API boundary and update `authStore` actions:

- `login` should call backend auth, then persist only safe client session data.
- `logout` should notify the backend if server-side sessions or tokens exist.
- Add a session restoration action that validates stored credentials with the backend before rendering protected data.
- Components should continue reading `authStore.isLoggedIn`, `authStore.user`, and `authStore.theme` rather than managing auth independently.

## UI Rules

- Keep validation feedback visible through both inline error text and `message.error`, matching `LoginModal.vue`.
- Clear password and error state on logout.
- Keep the login overlay mounted at the app shell level so unauthenticated users cannot interact with the workbench.

## Encoding Note

Many Chinese strings appear mojibaked in current source reads. When editing login copy, verify the actual file encoding and browser rendering before changing text. Avoid large copy rewrites unless the task is specifically about localization or encoding repair.
