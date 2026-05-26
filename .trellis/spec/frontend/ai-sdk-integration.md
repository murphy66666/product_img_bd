# AI Generation Integration

There is no real AI SDK integration in the current frontend. The product image generation flow is simulated in `src/components/ConfigPanel.vue`.

## Current Simulated Flow

`startGeneration()` in `ConfigPanel.vue`:

1. Reads the active `ChatSession` from `useChatStore()`.
2. Validates `uploadedImageUrl` and `prompt`.
3. Sets `chatStore.isGenerating = true`.
4. Adds a user `parameters` message.
5. Adds an assistant `loading` message with three steps.
6. Uses `setInterval` to advance progress.
7. Removes the loading message.
8. Adds a success assistant message.
9. Chooses mock Unsplash result URLs from hard-coded pools.
10. Adds generated images to `useGalleryStore()`.
11. Adds a `grid_result` message.
12. Persists chat state and fires `canvas-confetti`.

## Integration Boundary

When replacing this with real AI generation, keep orchestration in one boundary:

- Component validates UI state and starts the action.
- API/service module handles backend calls.
- Store actions update chat sessions and gallery.
- UI components render loading, progress, results, and errors.

Do not distribute one generation job across unrelated components.

## Required Real-World States

A backend-backed generation flow should model:

- queued
- uploading source image
- generating
- succeeded
- partially failed
- failed
- cancelled, if supported

The current `isGenerating` boolean is enough for the mock only. Replace or supplement it when the backend exposes job state.

## Data Mapping

Real results should map to existing UI concepts:

- source image URL or id
- prompt
- model
- resolution
- aspect ratio
- category
- generated image URLs
- created timestamp
- optional tags

## Avoid

- Do not import Vercel AI SDK or LangChain into the frontend unless the architecture explicitly requires client-side AI calls.
- Do not put API keys in Vue code.
- Do not keep large generated image blobs in localStorage.
- Do not leave mock Unsplash pools active in production generation paths.
