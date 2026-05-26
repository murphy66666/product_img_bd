# Frontend Development Guidelines

This frontend is a Vue 3 single page application for an AI product image generation workbench. It lives in `D:\g-code\frontend` and is separate from the FastAPI backend in `D:\g-code\backend`.

## Actual Tech Stack

- Framework: Vue 3 single-file components with `<script setup lang="ts">`
- Build tool: Vite
- State: Pinia option stores in `src/stores/`
- UI library: Ant Design Vue plus `@ant-design/icons-vue`
- Styling: UnoCSS utilities, Ant Design reset CSS, and global overrides in `src/style.css`
- Persistence: browser `localStorage`
- Current API integration: none in the checked frontend code; generation, login, chat sessions, and gallery data are local simulations

## Documentation Files

| File | Purpose |
| --- | --- |
| [directory-structure.md](./directory-structure.md) | Real frontend layout and ownership boundaries |
| [components.md](./components.md) | Vue component patterns, workbench layout, and UI responsibilities |
| [state-management.md](./state-management.md) | Pinia stores, localStorage keys, and mutation rules |
| [api-integration.md](./api-integration.md) | How to add backend API calls without breaking the current mock flow |
| [authentication.md](./authentication.md) | Current local login behavior and future backend-auth constraints |
| [css-layout.md](./css-layout.md) | UnoCSS, global CSS, Ant Design overrides, and fixed workbench layout |
| [type-safety.md](./type-safety.md) | TypeScript practices for stores, component props, and payloads |
| [hooks.md](./hooks.md) | Vue composable guidance; no composables exist yet |
| [ai-sdk-integration.md](./ai-sdk-integration.md) | Current simulated generation flow and future AI integration boundary |
| [orpc-usage.md](./orpc-usage.md) | oRPC is not currently used; keep this as a guardrail if introduced later |
| [quality.md](./quality.md) | Verification and review checklist |

## Must-Read Before Frontend Changes

Read these first for most frontend work:

1. [directory-structure.md](./directory-structure.md)
2. [components.md](./components.md)
3. [state-management.md](./state-management.md)
4. [css-layout.md](./css-layout.md)
5. [quality.md](./quality.md)

For backend integration, also read [api-integration.md](./api-integration.md) and [authentication.md](./authentication.md).

## Core Rules Summary

- Keep `App.vue` as the shell only: login overlay, top navigation, sidebar, config panel, and chat flow composition.
- Put persistent cross-component state in Pinia stores under `src/stores/`, not in sibling component refs.
- Keep generated image and chat history shape stable because current UI reads directly from store objects.
- Do not claim a real backend, AI SDK, or oRPC integration exists until the code actually calls it.
- Do not add raw backend-rendered HTML; this frontend owns the UI.
- Preserve the full-screen three-column workbench unless the task explicitly changes product design.
- Use Ant Design Vue components where the project already uses them: modal, dropdown, menu, slider, select, checkbox, and messages.
- Use UnoCSS utility classes for layout and visual state; reserve `src/style.css` for global resets and library overrides.
- Be careful with current text encoding. Several Chinese strings appear mojibaked in source reads; verify display in the browser before editing user-facing Chinese copy.

## Architecture Overview

```text
D:\g-code\frontend
  src/main.ts                 Vue app bootstrap: Pinia, Ant Design Vue, CSS imports
  src/App.vue                 Auth-gated workbench shell
  src/components/Navbar.vue   Mode switch, theme toggle, user menu
  src/components/Sidebar.vue  Chat history and generated gallery
  src/components/ConfigPanel.vue
                              Upload, presets, generation config, simulated generation
  src/components/ChatFlow.vue Chat transcript, result grid, lightbox/download actions
  src/components/LoginModal.vue
                              Local phone/password login overlay
  src/components/GenerationProgress.vue
                              Simulated generation stepper
  src/stores/auth.ts          Login state, user, theme in localStorage
  src/stores/chat.ts          Sessions, messages, active category, generation state
  src/stores/gallery.ts       Generated image gallery
```

## Verification Commands

From `D:\g-code\frontend`:

```bash
npm run build
npm run dev
```

The Vite dev server is configured in `vite.config.ts` to listen on `0.0.0.0:5173`.
