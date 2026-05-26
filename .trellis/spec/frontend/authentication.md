# Authentication

Authentication is currently a local demo flow, not a secure backend session.

## Current Behavior

`src/components/LoginModal.vue` owns the login form:

- Phone number is required and must match `^1[3-9]\d{9}$`.
- Password is required and must equal the hard-coded demo value `123456`.
- Optional remember-phone behavior writes `rememberedPhone` to localStorage.
- On success, it calls `authStore.login('phone', trimmedPhone)`.

`src/stores/auth.ts` persists:

- `isLoggedIn`
- `user`
- `theme`

`App.vue` renders the workbench only when `authStore.isLoggedIn` is true; otherwise it shows the login overlay and a blurred skeleton-like background.

## Security Constraints

- Do not treat this as production authentication.
- Do not add real secrets or API tokens to frontend source.
- Do not keep hard-coded production credentials in Vue files.
- Do not rely on localStorage for authorization decisions once backend APIs are protected.

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
