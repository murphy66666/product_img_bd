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

## Uploads

Current uploads use `FileReader.readAsDataURL()` and store a base64 data URL in the active session. A real backend upload should move large image bytes out of localStorage and return either a URL or file id.

Avoid storing large base64 strings in persistent browser state after backend uploads are available.
