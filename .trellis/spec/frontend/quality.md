# Frontend Quality Checklist

Use this checklist after frontend changes.

## Build Verification

From `D:\g-code\frontend` run:

```bash
npm run build
```

This runs `vue-tsc -b` and `vite build`.

For interactive verification run:

```bash
npm run dev
```

Open the Vite server at `http://localhost:5173` unless the terminal reports a different port.

## Manual Smoke Test

1. Load the app and confirm the login overlay appears.
2. Try invalid phone and invalid password; confirm inline and toast errors appear.
3. Login with a valid China mobile-style number and password `123456`.
4. Switch between `main` and `detail` modes in the navbar.
5. Create, rename, and delete a chat session; confirm delete uses a confirmation modal.
6. Select a preset or upload an image, edit prompt/config, and start generation.
7. Confirm loading progress appears, result images render, and gallery receives new items.
8. Open image lightbox and test download action.
9. Toggle light/dark theme and check major panels, modals, select, slider, and dropdown states.
10. Refresh the page and confirm persisted login/theme/session/gallery state behaves as expected.

## Review Focus

- Store mutations persist correctly and do not desync nested session config.
- Components do not duplicate data shapes already defined in stores.
- New backend calls have a clear API boundary and do not leak raw responses into templates.
- User-facing destructive actions still require confirmation.
- Large image data is not unnecessarily persisted to localStorage when backend upload exists.
- Chinese text renders correctly in the browser; current source reads show mojibake risk.

## Commands

Useful commands from `D:\g-code\frontend`:

```bash
npm run build
npm run dev
npm run preview
```

There is no configured unit test script in the current `package.json`.
