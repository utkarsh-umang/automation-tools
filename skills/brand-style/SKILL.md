---
name: brand-style
description: >-
  Applies this project's UI theme: dark chrome surfaces with blue gradients,
  light content areas, and the rocket logo. Use when styling interfaces,
  choosing colors, building components, laying out pages, or when the user
  mentions brand, theme, palette, colors, or visual design for this app.
---

# Brand Style

## Design Philosophy

**Dark chrome, light content.** The app uses a two-surface paradigm:
- **Chrome** (header, brand panels, card headers, full-page auth backgrounds) → deep navy-black with blue gradients
- **Content** (page body, data cards, form cards) → white / light gray

Blue is used heavily as both a gradient base on dark surfaces and as the primary action accent on light ones. There is no separate "dark mode" — this hybrid is the default.

---

## Logo

- File: `src/assets/logo.png` — rocket on near-black background, white body, blue flame
- Import: `import logo from '@/assets/logo.png'`
- Sizes in use:
  - Header: `h-9 w-9 rounded-lg`
  - Brand panel (large): `h-28 w-28 rounded-2xl`
  - Mobile inline: `h-10 w-10 rounded-xl`

---

## Color Palette

### Dark chrome colors

| Role | Value | Usage |
|------|-------|-------|
| Deep navy (base) | `#0a0f1e` | Page base, header bg, brand panel |
| Navy mid | `#0f1f4a` | Gradient midpoint on chrome surfaces |
| Dark form panel | `#0d1526` → `#111827` | Right-side dark panel on login |
| White text | `#ffffff` | Headings on dark |
| Subdued white | `rgba(255,255,255,0.65)` | Secondary text on dark (e.g. email in header) |
| Ghost white | `rgba(255,255,255,0.35)` | Tertiary text on dark (e.g. breadcrumb) |
| Very ghost white | `rgba(255,255,255,0.2)–0.3` | Fine print / decorative text on dark |

### Content colors (light surfaces)

| Role | Value | Usage |
|------|-------|-------|
| Page body | `#f9fafb` | Default page background behind cards |
| Card surface | `#ffffff` | Data cards, form card |
| Input resting | `#f9fafb` | Input bg before focus |
| Input focused | `#ffffff` | Input bg on focus |
| Primary text | `#111827` / `#0a0f1e` | Headings and labels on white |
| Muted text | `#6b7280` | Subtitles, hints, secondary labels |
| Border | `#e5e7eb` | Card borders, input borders on white |

### Blue accent

| Role | Value | Usage |
|------|-------|-------|
| Brand blue | `#2563eb` | Buttons, links, focus rings, highlights |
| Blue hover | `#1d4ed8` | Hover on filled blue controls |
| Blue pressed | `#1e40af` | Active / deeper hover state |
| Sky blue (on dark) | `#93c5fd` | Icon stroke and text inside blue-glass badges on dark |
| Blue glass bg | `rgba(37,99,235,0.25)` | Badge/pill background on dark chrome |
| Blue glass border | `rgba(37,99,235,0.5)` | Badge/pill border on dark chrome |
| Blue divider line | `rgba(37,99,235,0.2)` | Horizontal rules, header bottom border |
| Blue glow overlay | `rgba(37,99,235,0.15)` | Subtle box-shadow glow on chrome surfaces |

### Status colors

| State | Dot / icon | Text | Background | Border |
|-------|-----------|------|------------|--------|
| Success | `#22c55e` | `#15803d` | `#f0fdf4` | `#bbf7d0` |
| Error | `#f43f5e` | `#be123c` | `#fff1f2` | `#fecdd3` |

---

## Gradient System

All gradients in use:

```
Chrome header (horizontal sweep):
  linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 60%, #0a0f1e 100%)

Brand panel (diagonal):
  linear-gradient(135deg, #0a0f1e 0%, #0f1f4a 55%, #0a0f1e 100%)

Dark form / right panel:
  linear-gradient(160deg, #0d1526 0%, #111827 100%)

Blue glow orb (radial, decorative):
  radial-gradient(circle, rgba(37,99,235,0.25) 0%, transparent 70%)
  radial-gradient(circle, rgba(29,78,216,0.18) 0%, transparent 70%)  ← secondary orb

Blue grid overlay (on brand panel):
  backgroundImage: linear-gradient(rgba(37,99,235,0.06) 1px, transparent 1px),
                   linear-gradient(90deg, rgba(37,99,235,0.06) 1px, transparent 1px)
  backgroundSize: 48px 48px

Decorative blue divider line:
  linear-gradient(90deg, transparent, #2563eb, transparent)

Primary button:
  linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)

Primary button hover:
  linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%)

Avatar initial circle:
  linear-gradient(135deg, #2563eb, #1d4ed8)
```

---

## Component Recipes

### Dark chrome header

```
background: linear-gradient(90deg, #0a0f1e 0%, #0f1f4a 60%, #0a0f1e 100%)
borderBottom: 1px solid rgba(37,99,235,0.2)
boxShadow: 0 1px 0 rgba(37,99,235,0.15), 0 4px 20px rgba(0,0,0,0.4)
```

### Card on light page

```
backgroundColor: #ffffff
border: 1px solid #e5e7eb
borderRadius: rounded-xl
boxShadow: 0 1px 3px rgba(0,0,0,0.05)
```
Card header stripe (dark): same gradient as chrome header + `borderBottom: 1px solid rgba(37,99,235,0.2)`

### White form card floating on dark

```
backgroundColor: #ffffff
borderRadius: rounded-2xl
boxShadow: 0 0 0 1px rgba(255,255,255,0.06), 0 24px 48px rgba(0,0,0,0.5)
```

### Text input (on white card)

```
resting:  border 1px solid #e5e7eb, bg #f9fafb
focused:  border #2563eb, bg #ffffff, boxShadow 0 0 0 3px rgba(37,99,235,0.12)
```

### Primary button

```
background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)
boxShadow: 0 1px 2px rgba(37,99,235,0.4), 0 4px 12px rgba(37,99,235,0.2)
hover boxShadow: 0 1px 2px rgba(37,99,235,0.5), 0 6px 16px rgba(37,99,235,0.3)
text: #ffffff, font-semibold
```

### Ghost button on dark chrome

```
resting:  bg rgba(255,255,255,0.05), border 1px solid rgba(255,255,255,0.15), color rgba(255,255,255,0.7)
hover:    bg rgba(255,255,255,0.10), border rgba(255,255,255,0.25), color #ffffff
```

### Role / status badge on dark

```
background: rgba(37,99,235,0.25)
border: 1px solid rgba(37,99,235,0.5)
color: #93c5fd
borderRadius: rounded (small)
padding: px-1.5 py-0.5
fontSize: text-xs font-semibold
```

### Icon container on dark chrome

```
background: rgba(37,99,235,0.3)
border: 1px solid rgba(37,99,235,0.5)
borderRadius: rounded-lg
icon stroke: #93c5fd
```

### User avatar initial

```
background: linear-gradient(135deg, #2563eb, #1d4ed8)
color: #ffffff
borderRadius: rounded-full
h-7 w-7, text-xs font-semibold
content: first letter of email, uppercased
```

---

## Page Layout Patterns

### Authenticated app pages

```
┌─────────────────────────────────────────┐
│  Dark chrome header (logo + nav + user) │  ← dark gradient, blue glow border
├─────────────────────────────────────────┤
│                                         │
│   #f9fafb body — max-w-7xl centered    │  ← light gray page body
│   White cards with border + shadow     │
│                                         │
└─────────────────────────────────────────┘
```

### Login page (split layout, desktop)

```
┌──────────────────┬──────────────────────┐
│  Dark brand      │  Dark right panel    │
│  panel           │  (#0d1526→#111827)   │
│  (diagonal grad) │                      │
│  Logo + tagline  │  White card          │
│  Blue orbs/grid  │  (form floats on     │
│                  │   dark with shadow)  │
└──────────────────┴──────────────────────┘
```
Mobile: logo inline above the white card, full-width dark panel.

---

## CSS Variables (starting point for new UI)

```css
--color-chrome-base: #0a0f1e;
--color-chrome-mid: #0f1f4a;
--color-page-body: #f9fafb;
--color-surface: #ffffff;
--color-primary: #2563eb;
--color-primary-hover: #1d4ed8;
--color-primary-deep: #1e40af;
--color-accent-on-dark: #93c5fd;
--color-border: #e5e7eb;
--color-text: #111827;
--color-muted: #6b7280;
--color-success: #22c55e;
--color-error: #be123c;
```
