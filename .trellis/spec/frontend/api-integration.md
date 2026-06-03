# API Integration

The current frontend does not call the backend. All login, generation, chat sessions, and gallery records are local browser simulations.

## Current Evidence

- `src/main.ts` installs Pinia and Ant Design Vue only.
- `src/stores/*.ts` read and write `localStorage` directly.
- `src/components/ConfigPanel.vue` simulates generation with `setInterval`, hard-coded Unsplash result pools, and `canvas-confetti`.
- No `src/api/`, `src/services/`, `fetch`, Axios, oRPC client, or generated API client exists in the frontend source.

## Adding Backend Calls

When real FastAPI endpoints are introduced, add a small API boundary instead of calling `fetch` from templates:

```text
src/api/
  client.ts        base URL, JSON handling, auth headers, errors
  generation.ts    generation request/result functions
  auth.ts          login/session functions if backend auth exists
```

Keep the component flow stable:

1. Validate form state in the component or a composable.
2. Convert Pinia session config into the backend request DTO.
3. Call the API module.
4. Map the response back into `ChatMessage`, `GeneratedImage`, or a store action input.
5. Persist through Pinia actions.

All JSON requests must send `Content-Type: application/json; charset=UTF-8`. Do not use GBK, GB2312, or workstation-local encodings at the API boundary.

## Error Handling

- Surface user-facing failures with Ant Design Vue `message.error` or an inline error state.
- Always clear `chatStore.isGenerating` in a `finally` block when replacing the simulated generation interval with real async work.
- Keep partial failure behavior explicit: if some images fail, decide whether the gallery stores successful images, an error bubble, or both.

## Data Contract Guidance

Stable frontend concepts that backend responses should map to:

- Generation category: `main` or `detail`
- Model identifier
- Aspect ratio string such as `1:1` or `9:16`
- Resolution string such as `2k` or `4k`
- Quantity
- Prompt
- Uploaded original image URL or backend file id
- Generated image URLs and metadata

Do not change JSON response shape casually once the backend and frontend are connected; project rules require stable JSON interfaces for other systems.

## Scenario: UTF-8 API Boundary

### 1. Scope / Trigger
- Trigger: Any frontend API client change that sends JSON to the FastAPI backend.

### 2. Signatures
- API client: `src/api/client.ts`
- Request header: `Content-Type: application/json; charset=UTF-8`
- Backend response header: `Content-Type: application/json; charset=utf-8`

### 3. Contracts
- `FormData` uploads must let the browser set multipart boundaries and must not force a JSON content type.
- JSON request bodies must explicitly declare UTF-8.
- API response parsing assumes backend JSON is UTF-8 and uses the stable `{ success, data, message }` envelope.

### 4. Validation & Error Matrix
- JSON request missing charset -> update `src/api/client.ts` before adding endpoint-specific callers.
- Upload request with forced JSON content type -> backend cannot parse multipart and must be fixed in the client.
- Backend returns non-JSON or malformed JSON -> client raises `ApiError`.

### 5. Good/Base/Bad Cases
- Good: `request('/sessions', { method: 'POST', body: JSON.stringify(payload) })` sends UTF-8 JSON.
- Base: `request('/uploads', { method: 'POST', body: formData })` leaves multipart headers to the browser.
- Bad: Endpoint code calls `fetch()` directly and sends `application/json` without `charset=UTF-8`.

### 6. Tests Required
- Frontend `npm run build` must pass after API client changes.
- Backend route test should assert JSON response content type includes `charset=utf-8`.

### 7. Wrong vs Correct

#### Wrong
```ts
headers.set('Content-Type', 'application/json')
```

#### Correct
```ts
headers.set('Content-Type', 'application/json; charset=UTF-8')
```

## Scenario: New Chat Session Route and API

### 1. Scope / Trigger
- Trigger: creating a conversation now spans Vue Router, Pinia, FastAPI, and MySQL.

### 2. Signatures
- Frontend route: `/sessions/:sessionId`
- API function: `createSessionApi(category, title?)`
- Backend API: `POST /api/v1/sessions`

### 3. Contracts
- `chatStore.createNewSession()` must call `createSessionApi()` when `isApiBacked` is true.
- In API-backed mode, creation failure must surface to the UI; do not silently create a local-only session.
- Selecting or creating a session should update `activeSessionId`; the workspace route watcher then replaces the URL with `/sessions/:sessionId`.

### 4. Validation & Error Matrix
- API returns `401` -> auth flow must re-login or fall back only during demo/offline mode.
- API returns `503` -> show a user-visible create failure and keep the current session.
- Unknown route session id -> keep the loaded active session and normalize the URL to it.

### 5. Good/Base/Bad Cases
- Good: User clicks new session, API persists it, store inserts it, and URL changes to `/sessions/<id>`.
- Base: User opens `/sessions/<id>` directly after login; store selects that session if present.
- Bad: User clicks new session while API-backed and DB is down; do not add an unsaved session to the list.

### 6. Tests Required
- Frontend build/type-check must pass.
- Backend route tests must cover success and database-unavailable responses.

### 7. Wrong vs Correct

#### Wrong
```ts
try {
  session = await createSessionApi(category)
} catch {
  session = createLocalSession(category)
}
```

#### Correct
```ts
if (this.isApiBacked) {
  session = await createSessionApi(category)
} else {
  session = createLocalSession(category)
}
```

## Uploads

Current uploads use `FileReader.readAsDataURL()` and store a base64 data URL in the active session. A real backend upload should move large image bytes out of localStorage and return either a URL or file id.

Avoid storing large base64 strings in persistent browser state after backend uploads are available.

## Scenario: GPT Image 2 Edit-Image Generation

### 1. Scope / Trigger
- Trigger: Generation uses uploaded product/reference images and the backend calls an OpenAI-compatible `/images/edits` provider endpoint.

### 2. Signatures
- Upload API: `POST /api/v1/uploads/images`
- Generation API: `POST /api/v1/generation/jobs`
- Frontend request fields: `model`, `prompt`, `sourceImageIds`, `size`, `quality`, `n`, `outputFormat`, `stream`, `sessionId`.

### 3. Contracts
- `model` is `gpt-image-2` for this flow.
- The browser uploads files first and stores backend upload IDs, not local filesystem paths.
- `sourceImageIds` must be non-empty before starting generation.
- `outputFormat` is camelCase in frontend JSON and maps to provider `output_format` in the backend.
- Gallery displays backend local generated image URLs, not provider OSS URLs.

### 4. Validation & Error Matrix
- No uploaded source image -> show a user-visible warning and do not call generation API.
- Upload API failure -> use local preview only for display; do not submit a provider edit job without an upload ID.
- Backend returns `401` -> logout or re-login flow.
- Backend generation failure -> clear `isGenerating` in `finally`, remove any loading message, and show the real error. Do not synthesize local demo images after a submitted backend generation job fails.

### 5. Good/Base/Bad Cases
- Good: User uploads three images, frontend submits three upload IDs, and result images render from local backend public URLs.
- Base: Provider returns fewer images than requested; frontend renders the returned images and message uses actual image count.
- Bad: Frontend sends `C:\Users\...` paths or stores large base64 source images in persistent session state.
- Bad: Backend generation returns `failed`, times out, or rejects provider config, and the frontend fills the result grid with local Unsplash/demo images.

### 6. Tests Required
- `npm run build` must pass.
- Manual UI smoke test should cover multi-image upload, payload shape, generation polling, and gallery rendering.
- Regression check should confirm failed generation displays an error message and does not call local mock/demo image builders.

### 7. Wrong vs Correct

#### Wrong
```ts
await createGenerationJobApi({ sourceImageUrl: file.name })
```

#### Correct
```ts
const image = await uploadImageApi(file)
await createGenerationJobApi({ sourceImageIds: [image.id], outputFormat: 'png' })
```

## Scenario: Smart Templates API

### 1. Scope / Trigger
- Trigger: Smart templates now come from the backend and are filtered by database type instead of being hard-coded in `ConfigPanel.vue`.

### 2. Signatures
- API function: `listSmartTemplatesApi(type)`
- Backend API: `GET /api/v1/templates?type=1|2`
- UI mapping: `main -> type=1`, `detail -> type=2`

### 3. Contracts
- Response envelope: `{ success, data: { templates }, message }`.
- Template fields: `id`, `name`, `imageUrl`, `prompt`, `model`, `aspectRatio`, `resolution`, `quantity`, `type`.
- `type=1` means product main image templates; `type=2` means product detail image templates.

### 4. Validation & Error Matrix
- Missing `type` -> backend may return all enabled templates.
- `type` outside `1|2` -> backend returns `422`.
- API failure -> frontend shows a user-visible load failure and does not silently use hard-coded templates as source data.

### 5. Good/Base/Bad Cases
- Good: Switching from main to detail mode refetches templates with `type=2`.
- Base: Main mode loads only `type=1` templates.
- Bad: A `detail` template appears in main mode because frontend forgot the category-to-type mapping.

### 6. Tests Required
- Backend route test asserts `type=1` filtering and camelCase fields.
- Backend route test rejects invalid `type=3`.
- Frontend build/type-check must pass after API type changes.

### 7. Wrong vs Correct

#### Wrong
```ts
const templates = [{ name: 'Beauty skincare' }]
```

#### Correct
```ts
const type = chatStore.activeCategory === 'main' ? 1 : 2
const templates = await listSmartTemplatesApi(type)
```
