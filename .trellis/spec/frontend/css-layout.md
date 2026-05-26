# CSS and Layout

The frontend uses UnoCSS utility classes for most layout and visual styling, with global CSS reserved for app-wide reset and Ant Design overrides.

## CSS Entry Order

`src/main.ts` imports styles in this order:

1. `virtual:uno.css`
2. `ant-design-vue/dist/reset.css`
3. `./style.css`

Keep this order unless there is a specific override reason. `style.css` intentionally comes last so global overrides can affect Ant Design components.

## Workbench Layout

The app is a fixed full-screen workbench:

- `html`, `body`, and `#app` are `100vw`/`100vh` with hidden overflow.
- `App.vue` uses `w-screen h-screen flex flex-col overflow-hidden`.
- Authenticated layout is `Navbar` plus a horizontal flex body.
- `Sidebar` is fixed width `w-72`.
- `ConfigPanel` is fixed width `w-80`.
- `ChatFlow` fills remaining space.

When changing layout, test at desktop and narrow widths. The current code is desktop-workbench oriented and does not implement a complete mobile navigation model.

## UnoCSS

`uno.config.ts` enables:

- `presetUno`
- `presetAttributify`
- `presetIcons`
- `transformerDirectives`
- `transformerVariantGroup`

Theme colors define `brand.dark`, `brand.card`, `brand.border`, `brand.violet`, and `brand.cyan`.

Shortcuts currently include:

- `glass-card`
- `glass-card-hover`
- `btn-aurora`
- `input-glow`

Use shortcuts for repeated visual primitives, but do not hide one-off layout decisions inside new shortcuts.

## Ant Design Overrides

Global overrides in `src/style.css` customize modal, select, and scrollbar appearance. Component-scoped CSS uses `:deep()` for Ant Design internals, such as slider and modal content.

When modifying Ant Design components:

- Prefer component props first.
- Use scoped `:deep()` for component-specific overrides.
- Use `src/style.css` only for global cross-app overrides.

## Theme Pattern

Most components branch on `authStore.theme === 'light'` in class bindings. Preserve this pattern when adding themed UI so light and dark states stay explicit.

## Visual Asset Rules

The current app uses remote Unsplash images for mock source and generated product images. If real backend generation is added, replace mock URLs with backend outputs but preserve stable image sizing (`object-cover`, `aspect-square`, modal `object-contain`) to avoid layout jumps.
