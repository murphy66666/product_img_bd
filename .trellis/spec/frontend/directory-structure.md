# Frontend Directory Structure

The frontend project is `D:\g-code\frontend`. It is a compact Vue SPA, not a route-heavy application.

## Root Files

- `package.json`: Vite scripts and dependencies. Current scripts are `dev`, `build`, and `preview`.
- `vite.config.ts`: registers Vue and UnoCSS plugins, serves on `0.0.0.0:5173`.
- `uno.config.ts`: project design tokens, animations, and utility shortcuts such as `glass-card`, `btn-aurora`, and `input-glow`.
- `index.html`: Vite HTML entry.
- `src/main.ts`: creates the Vue app, installs Pinia and Ant Design Vue, then mounts `App.vue`.
- `src/style.css`: global font import, full-window reset, scrollbar styling, glass input styles, and Ant Design overrides.

## Source Layout

```text
src/
  App.vue
  main.ts
  style.css
  assets/
  components/
    ChatFlow.vue
    ConfigPanel.vue
    GenerationProgress.vue
    HelloWorld.vue
    LoginModal.vue
    Navbar.vue
    Sidebar.vue
  stores/
    auth.ts
    chat.ts
    gallery.ts
```

## Ownership Boundaries

- `App.vue` owns page-level composition and auth gating only.
- `components/` owns visual workflows and interaction handlers.
- `stores/` owns persisted state and cross-component actions.
- `style.css` owns app-wide CSS and third-party library overrides.
- `uno.config.ts` owns reusable utility shortcuts and theme tokens.

## Current Unused or Legacy Files

`src/components/HelloWorld.vue` and default Vite assets (`vite.svg`, `vue.svg`) are present but not part of the current app shell. Do not use them as implementation examples for the product workbench.

## Adding Files

Add a new component when a visible workflow grows beyond one responsibility. Keep product workflows modular: for example, image upload, prompt editing, result grid, and gallery actions should not all be merged into `App.vue`.

Add a composable under `src/composables/` only when behavior is shared by multiple components or needs lifecycle cleanup. No composables exist in the current codebase, so do not create one for single-use logic.

Add API modules under `src/api/` or `src/services/` when real backend calls are introduced. Keep HTTP details out of Vue templates and Pinia state definitions.
