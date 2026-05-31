# State Management

The frontend uses Pinia option stores in `src/stores/`. Durable state is persisted to browser storage with explicit keys.

## Stores

### `auth.ts`

Store id: `auth`

State:

- `isLoggedIn`: initialized from whether stored `authToken` and `authUser` both exist and parse successfully
- `user`: parsed from stored `authUser`, or `null`
- `theme`: `dark` or `light`, initialized from `localStorage.theme` with `dark` default

Actions:

- `login(username, password, rememberMe?)`: calls backend auth, sets the bearer token, and stores `authToken`/`authUser` in localStorage when remembered or sessionStorage otherwise.
- `logout()`: calls backend logout, clears auth storage from both localStorage and sessionStorage, and leaves theme intact.
- `toggleTheme()`: toggles and persists theme.

### `chat.ts`

Store id: `chat`

State:

- `sessions`: parsed from `localStorage.chat_sessions`, otherwise preset mock sessions.
- `activeSessionId`: parsed from `localStorage.active_session_id`, otherwise `s-1`.
- `activeCategory`: `main` or `detail`.
- `isGenerating`: transient boolean for generation UI.

Getters:

- `activeSession`
- `filteredSessions`

Actions own category switching, session creation/deletion/rename, message creation, config merging, and persistence.

### `gallery.ts`

Store id: `gallery`

State:

- `images`: parsed from `localStorage.gallery_images`, otherwise preset mock gallery images.

Actions:

- `addImage()` creates an id/date and persists.
- `deleteImage()` removes an image and persists.

## Persistence Keys

Current localStorage keys:

- `authToken`
- `authUser`
- `theme`
- `rememberedPhone`
- `chat_sessions`
- `active_session_id`
- `gallery_images`

Current sessionStorage keys:

- `authToken`
- `authUser`

When changing these keys, provide migration or clear fallback behavior. Existing users can have old data in the browser. If adding a token-backed auth flow, remember that an in-memory API client token must be rehydrated from storage during store initialization.

## Mutation Rules

- Use store actions for reusable mutations.
- If a component directly updates nested session config, call `chatStore.saveToStorage()` immediately after the mutation.
- Keep `isGenerating` transient. Do not persist it unless the product explicitly supports resumable generation.
- When adding new fields to `ChatSession`, update preset sessions, session creation, parameter bubbles, and any future backend DTO mapping together.

## Type Rules

- Avoid `payload?: any` for new message types. The current `ChatMessage.payload` is loose because multiple mock bubble types share one field; new code should add discriminated message interfaces before adding more payload shapes.
- Keep `category` as the existing union `'main' | 'detail'` unless the product adds a third generation mode.
- Keep generated image metadata in `GeneratedImage`; do not duplicate gallery image shapes inside components.

## Backend Integration Impact

When replacing local mocks with backend data, preserve UI-facing shape or introduce explicit mapping functions. Do not let raw backend responses leak into components, because current components assume fields like `messages`, `config`, `images`, `prompt`, `aspectRatio`, and `createdAt` are always present.
