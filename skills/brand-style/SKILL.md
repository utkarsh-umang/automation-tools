---
name: brand-style
description: >-
  Applies this project's light UI theme and brand colors (white surfaces, dark
  text, blue accent). Use when styling interfaces, choosing colors, building
  components, or when the user mentions brand, theme, palette, or visual design
  for this app.
---

# Brand style

## Theme

Default to a **light theme**: bright backgrounds, dark text, blue for interactive emphasis. Do not ship a dark theme unless the user explicitly asks.

## Palette

| Role | Hex | Usage |
|------|-----|--------|
| **Background** | `#ffffff` | Page and card surfaces, main canvas |
| **Text / ink** | `#1a1a1a` | Body copy, headings, icons on light backgrounds |
| **Accent (brand blue)** | `#2563eb` | Primary buttons, links, focus rings, selected states, key highlights |

Supporting neutrals (when you need more than binary light/dark):

- **Borders / dividers**: light gray around `#e5e7eb`–`#f3f4f6` on white
- **Muted text**: mid gray around `#6b7280` for secondary labels and hints
- **Hover on primary**: slightly darker blue (e.g. `#1d4ed8`) for filled blue controls

## Rules

1. **Surfaces**: Prefer white (`#ffffff`) for primary surfaces; use subtle gray fills only for secondary panels, stripes, or disabled areas—not as the default page background.
2. **Text**: Use `#1a1a1a` for primary text; avoid pure black (`#000000`) unless matching existing code.
3. **Blue**: Use `#2563eb` for primary actions, links, and focus—one strong accent, not competing primaries.
4. **Contrast**: Keep text on `#ffffff` at WCAG-friendly contrast; avoid light gray text on white for essential content.
5. **Code / tokens**: When adding CSS variables or design tokens, name roles (`--color-background`, `--color-foreground`, `--color-primary`) and map them to the hex values above so the theme stays consistent.

## Quick reference (CSS variables)

Use as a starting point for new UI:

```css
--color-background: #ffffff;
--color-foreground: #1a1a1a;
--color-primary: #2563eb;
--color-primary-hover: #1d4ed8;
--color-border: #e5e7eb;
--color-muted: #6b7280;
```

Adapt naming to the project's existing token system; preserve these hex relationships.
