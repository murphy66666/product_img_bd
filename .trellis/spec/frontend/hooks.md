# Vue Composables

The current frontend does not have a `src/composables/` directory and does not use React hooks. In Vue, shared reactive behavior should be implemented as composables only when reuse or lifecycle isolation justifies it.

## Current Pattern

Components currently keep single-use behavior local:

- `ChatFlow.vue` owns scrolling and lightbox state.
- `ConfigPanel.vue` owns upload handling and simulated generation orchestration.
- `LoginModal.vue` owns form validation refs and error clearing watchers.
- Pinia stores own persistent cross-component state.

Do not move code into a composable just to make a file smaller. First check whether at least two components need the same behavior.

## When to Add a Composable

Create `src/composables/useX.ts` when:

- Multiple components share the same browser lifecycle behavior.
- The logic needs cleanup, cancellation, or retry handling.
- API interaction state would otherwise be duplicated.
- The behavior is independent of rendering and can be tested separately.

Good future candidates:

- `useImageUpload` for validation, preview, and backend upload.
- `useGenerationJob` for async generation polling or streaming.
- `useAutoScroll` if multiple transcript-like panes are added.

## Rules

- Keep composables framework-native: use Vue refs, computed values, lifecycle hooks, and cleanup.
- Do not store global business state in composables when Pinia is the right owner.
- Return a small explicit API rather than a large object of unrelated helpers.
- Keep API clients outside composables if multiple stores or services need them.

## Anti-Patterns

- Do not create React-style `useEffect` patterns.
- Do not hide Pinia mutations inside composables without clear naming.
- Do not create a composable for one component's template-only boolean state.
