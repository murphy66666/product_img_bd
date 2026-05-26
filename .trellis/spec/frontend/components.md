# Vue Components

The UI is built with Vue 3 SFCs using `<script setup lang="ts">`. Components use Pinia stores directly when they participate in the shared workbench state.

## Shell Composition

`src/App.vue` composes the main application:

- `LoginModal` is always mounted and intercepts unauthenticated users.
- `Navbar`, `Sidebar`, `ConfigPanel`, and `ChatFlow` render only when `authStore.isLoggedIn` is true.
- The authenticated layout is a fixed full-screen flex workbench: top nav plus a left sidebar, center config panel, and right chat/result area.

Do not move business workflow logic into `App.vue`. Keep it as the page shell.

## Component Responsibilities

- `Navbar.vue`: product identity, `main`/`detail` mode switch, theme toggle, user balance display, logout menu.
- `Sidebar.vue`: switches between chat history and gallery, creates/renames/deletes sessions, previews/downloads gallery images.
- `ConfigPanel.vue`: preset templates, image upload, model/aspect/resolution/quantity/prompt config, and the current simulated generation flow.
- `ChatFlow.vue`: transcript rendering, loading bubble, parameter cards, generated image grid, lightbox preview, download, and prompt reuse.
- `LoginModal.vue`: local phone/password validation, remember-phone behavior, login overlay.
- `GenerationProgress.vue`: presentational component for simulated generation steps.

## Local Patterns

- Import stores at the top of `<script setup>` and use them directly in templates.
- Use `ref`, `computed`, `watch`, `onMounted`, and `nextTick` from Vue where needed.
- Use Ant Design Vue feedback APIs (`message`, `Modal`) for user-visible confirmations and toasts.
- Use Ant Design Vue components in templates with Vue binding syntax such as `v-model:open`, `v-model:value`, and `:wrapClassName`.
- Use icons from `@ant-design/icons-vue`; the current project does not use lucide.

## Interaction Rules

- Destructive UI actions need confirmation. `Sidebar.vue` uses `Modal.confirm` before deleting a chat session.
- Generation must validate required config before mutating chat history. `ConfigPanel.vue` currently requires an uploaded image and non-empty prompt.
- Actions that mutate persisted state must call the relevant store action or `saveToStorage()` immediately.
- For DOM-only operations such as downloads, create and remove temporary anchors in the handler. Keep this behavior out of stores.

## Template Rules

- Prefer semantic buttons for clickable actions. The current code has some clickable `div`/`span` controls; new work should use `button` when the element performs an action.
- Keep repeated UI driven by arrays (`templates`, `aspectRatios`, `models`, `resolutions`) instead of duplicating template blocks.
- Keep image grids dimensionally stable with `aspect-square`, fixed grid columns, and object-fit classes.
- Keep modal content in Vue templates, not generated HTML strings.

## Common Mistakes

- Do not add route assumptions. There is no `vue-router` setup in `main.ts` even though `vue-router` is installed.
- Do not introduce React, Next.js, or JSX patterns.
- Do not bypass Pinia by writing independent localStorage mutations from many components unless the state is truly component-local.
- Do not treat the current mock generation as a real backend contract.
