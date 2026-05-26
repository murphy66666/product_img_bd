# Type Safety

The frontend is TypeScript-based but currently has loose areas that should be tightened during feature work.

## Current Config

- Vue SFCs use `<script setup lang="ts">`.
- `package.json` build runs `vue-tsc -b && vite build`.
- Store interfaces are declared near their Pinia stores.

## Existing Types

`src/stores/auth.ts`:

- `User`

`src/stores/chat.ts`:

- `ChatMessage`
- `ChatSession`

`src/stores/gallery.ts`:

- `GeneratedImage`

Use these existing interfaces instead of redefining matching shapes in components.

## New Code Rules

- Keep generation category typed as `'main' | 'detail'`.
- Keep message sender typed as `'user' | 'assistant'`.
- Add explicit interfaces for new API DTOs and map them into store interfaces.
- Avoid adding new `any`. The current `ChatMessage.payload?: any` should be treated as legacy technical debt.
- Prefer discriminated unions for new chat message payloads.

Example direction:

```ts
type ChatMessageType = 'message' | 'parameters' | 'grid_result' | 'loading'
```

If the message system grows, split message types so each `type` has a known payload shape.

## localStorage Parsing

Current stores parse localStorage without schema validation. When touching persistence, add defensive parsing around user-controlled stored JSON so corrupted browser data does not crash app startup.

Suggested pattern:

- Read raw string.
- Try `JSON.parse`.
- Validate minimum shape.
- Fall back to preset defaults or empty state.

## Component Props

`GenerationProgress.vue` demonstrates typed props:

```ts
const props = defineProps<{
  currentStep: number
  steps: string[]
}>()
```

Follow this pattern for new presentational components.

## API Integration

When backend calls are introduced, do not let untyped response JSON flow into Pinia. Define response types or generated client types at the API boundary, then convert into frontend store models.
