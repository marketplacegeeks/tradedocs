---
## name: loopai-design-system description: > Apply this skill for ALL UI and frontend tasks. Enforces the LoopAI CRM aesthetic — a soft-pastel, card-based, AI-powered SaaS dashboard style by Phenomenon Studio. Use when building dashboards, CRM screens, job boards, settings pages, data tables, sidebars, modals, onboarding flows, or any product UI. Produces clean, premium, production-grade interfaces with strong typographic hierarchy and calm visual depth.
# LoopAI Design System Skill
Reference aesthetic: LoopAI CRM Dashboard by Phenomenon Studio (Dribbble) https://dribbble.com/shots/25961490-LoopAI-CRM-Dashboard-for-B2B-SaaS
Before writing any UI code, internalize and apply every rule in this document. This is the single source of truth for all visual decisions.
---
## 1. Aesthetic Direction
**Style**: Soft-pastel, calm, premium B2B SaaS. Clean but warm — not sterile. **Mood**: Organized clarity. Like a well-designed Notion meets a modern CRM. **Audience**: Professional users — freelancers, PMs, founders, recruiters. **One unforgettable thing**: Pastel accent chips + white cards floating on a soft background — everything feels light, breathable, and intentional.
This is NOT a dark-mode brutalist app. It is NOT a purple-gradient AI startup. It is soft, organized, human, and quietly sophisticated.
---
## 2. Color Palette
Use CSS variables. Apply these consistently across every component.
```javascript
:root {
  /* Backgrounds */
  --bg-base: #F4F5F7;          /* soft warm gray — main page background */
  --bg-surface: #FFFFFF;       /* pure white — cards, panels, modals */
  --bg-sidebar: #FFFFFF;       /* white sidebar with subtle left border */
  --bg-hover: #F0F1F5;         /* on hover state for rows, nav items */
  --bg-input: #F8F9FB;         /* input field backgrounds */

  /* Pastel accent chips — use for tags, status badges, category labels */
  --pastel-blue: #DDE8FF;      /* blue chip bg */
  --pastel-blue-text: #3B6FE8;
  --pastel-green: #D6F5E3;     /* green chip bg */
  --pastel-green-text: #1A8A4A;
  --pastel-yellow: #FFF3D6;    /* yellow/amber chip */
  --pastel-yellow-text: #B57B00;
  --pastel-pink: #FFE0EC;      /* pink chip */
  --pastel-pink-text: #C0335A;
  --pastel-purple: #EDE0FF;    /* purple chip */
  --pastel-purple-text: #6B35C2;
  --pastel-orange: #FFE8D6;    /* orange chip */
  --pastel-orange-text: #B85C00;

  /* Primary action color */
  --primary: #4F6EF7;          /* medium blue — buttons, links, active nav */
  --primary-hover: #3A58E0;
  --primary-light: #EEF1FF;    /* light blue tint for selected rows */

  /* Text hierarchy */
  --text-primary: #1A1D23;     /* headings, bold labels */
  --text-secondary: #5A6070;   /* body text, descriptions */
  --text-muted: #9BA3B5;       /* timestamps, placeholders, helper text */
  --text-inverse: #FFFFFF;

  /* Borders */
  --border-light: #ECEEF2;     /* card borders, dividers */
  --border-medium: #D8DCE6;    /* input borders, table lines */

  /* Shadows */
  --shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
  --shadow-dropdown: 0 8px 24px rgba(0,0,0,0.10);
  --shadow-modal: 0 16px 48px rgba(0,0,0,0.14);
}

```
---
## 3. Typography
**Font pairing** (import from Google Fonts):
- **Display / Headings**: `Plus Jakarta Sans` — modern, geometric warmth
- **Body / UI**: `DM Sans` — clean, highly legible, friendly
```javascript
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

```
**Never use**: Inter, Roboto, Arial, system-ui, or any generic sans-serif.
### Type Scale
| Role | Font | Size | Weight | Color |
| --- | --- | --- | --- | --- |
| Page title | Plus Jakarta Sans | 22px | 700 | `--text-primary` |
| Section heading | Plus Jakarta Sans | 16px | 600 | `--text-primary` |
| Card title | Plus Jakarta Sans | 14px | 600 | `--text-primary` |
| Body text | DM Sans | 14px | 400 | `--text-secondary` |
| Small label | DM Sans | 12px | 500 | `--text-muted` |
| Metric / KPI | Plus Jakarta Sans | 28–36px | 700 | `--text-primary` |
| Chip / Badge | DM Sans | 11px | 600 | (pastel color) |
---
## 4. Layout Structure
### Sidebar (Left Nav)
- Width: 220px fixed
- Background: `--bg-sidebar`
- Right border: `1px solid var(--border-light)`
- Logo at top with product name in Plus Jakarta Sans 700
- Nav items: 40px height, 12px horizontal padding, 8px border-radius on hover
- Active nav item: `--primary-light` background, `--primary` text and icon
- Icon + label layout, icons 18px
- User avatar + name at bottom
### Main Content Area
- Background: `--bg-base`
- Padding: 32px
- Max width: none (full fluid)
- Top bar: page title left, action buttons right
### Cards
- Background: `--bg-surface`
- Border: `1px solid var(--border-light)`
- Border-radius: 14px
- Padding: 20px 24px
- Shadow: `--shadow-card`
- Never use colored card backgrounds — keep all cards white
### Grid / Dashboard Layout
- Use CSS Grid: 12-column grid with 20px gap
- KPI stat cards: span 3 cols each (4 across)
- Charts: span 6–8 cols
- Activity feed / list panels: span 4–6 cols
---
## 5. Component Patterns
### KPI Stat Card
```javascript
┌─────────────────────────────┐
│  [Icon in pastel chip]      │
│                             │
│  $48,200                    │  ← 32px bold, Plus Jakarta Sans
│  Total Revenue              │  ← 13px muted
│                             │
│  ↑ 12.4%  vs last month     │  ← green pastel chip for positive delta
└─────────────────────────────┘

```
- Icon wrapped in a 36x36 pastel-colored rounded square (border-radius: 10px)
- Delta shown as small pastel chip (green for positive, red/pink for negative)
### Data Table
- Header row: `--bg-base` background, 12px uppercase DM Sans 600, `--text-muted`
- Row height: 52px
- Alternating rows: no zebra striping — use hover state only
- Row hover: `--bg-hover`
- Selected row: `--primary-light` background
- Status columns use pastel chips (not colored dots)
- Last column: action icons (edit/delete) appear only on row hover
### Pastel Chips / Badges
```javascript
.chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 100px;
  font-family: 'DM Sans', sans-serif;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.chip-blue   { background: var(--pastel-blue);   color: var(--pastel-blue-text); }
.chip-green  { background: var(--pastel-green);  color: var(--pastel-green-text); }
.chip-yellow { background: var(--pastel-yellow); color: var(--pastel-yellow-text); }
.chip-pink   { background: var(--pastel-pink);   color: var(--pastel-pink-text); }
.chip-purple { background: var(--pastel-purple); color: var(--pastel-purple-text); }

```
Use chips for: status, category, platform, deal stage, tags. Never use plain colored text or solid dark badges.
### Buttons
```javascript
/* Primary */
.btn-primary {
  background: var(--primary);
  color: white;
  border-radius: 8px;
  padding: 9px 18px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: background 0.15s ease;
}
.btn-primary:hover { background: var(--primary-hover); }

/* Ghost / Secondary */
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-medium);
  border-radius: 8px;
  padding: 9px 18px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  font-weight: 500;
}
.btn-ghost:hover { background: var(--bg-hover); }

```
### Input Fields
```javascript
.input {
  background: var(--bg-input);
  border: 1px solid var(--border-medium);
  border-radius: 8px;
  padding: 9px 14px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s ease;
}
.input:focus { border-color: var(--primary); }

```
### Search Bar
- Prepend a search icon inside the input
- Placeholder: `--text-muted`
- Background: `--bg-input`
- Optional: filter icon button to the right
### Avatar
- Circular, 32px default, 40px for profile areas
- If no image: colored initial circle using a pastel chip color as background
- Name + role stacked next to avatar where space allows
### Progress / Pipeline
- Thin horizontal bar (6px height), border-radius 100px
- Track: `--border-light`
- Fill: `--primary` or contextual pastel (green for complete, yellow for in-progress)
- Show percentage label to the right
---
## 6. Motion & Interactions
Keep animations subtle and purposeful. This is a professional tool, not a portfolio site.
```javascript
/* Page / card load — staggered fade up */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.card { animation: fadeUp 0.3s ease both; }
.card:nth-child(1) { animation-delay: 0.05s; }
.card:nth-child(2) { animation-delay: 0.10s; }
.card:nth-child(3) { animation-delay: 0.15s; }
.card:nth-child(4) { animation-delay: 0.20s; }

/* Hover transitions */
* { transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease; }

/* Card hover lift */
.card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.08); transform: translateY(-1px); }

```
Micro-interactions to always include:
- Sidebar nav item: background fill on hover, left border indicator on active
- Table rows: background on hover, cursor pointer
- Buttons: color darken on hover
- Cards: subtle lift on hover (translateY -1px)
- Chips: no interaction (purely informational)
---
## 7. Icons
Use **Lucide Icons** (already available in React via `lucide-react`, or via CDN for HTML).
- Size: 16px for inline UI, 18px for nav, 20px for feature icons
- Stroke width: 1.5 (thinner looks more refined)
- Color: inherit from parent or `--text-muted` for decorative icons
Never use emoji as icons in professional UI.
---
## 8. Spacing System
Use a consistent 4px base grid:
| Token | Value | Use |
| --- | --- | --- |
| xs | 4px | tight gaps, icon padding |
| sm | 8px | between inline elements |
| md | 16px | card internal spacing |
| lg | 24px | between sections |
| xl | 32px | page padding |
| 2xl | 48px | section breaks |
---
## 9. Specific Screen Patterns (for PMBoard / Job Boards)
Since this skill is used for a PM job board, apply these specific patterns:
**Job listing row**: Company logo (32px circle) + Job title (600 weight) + Company name (muted) + Location chip + Salary chip + Posted date (muted right-aligned)
**Recruiter card**: Avatar + Name + Title + Company + Platform chips (Upwork, LinkedIn, etc.) + "View contact" CTA button
**Pipeline / kanban**: Horizontal scroll, each column 280px wide, cards draggable, column headers use pastel chips for stage names
**Analytics card**: Single metric large + sparkline chart below + delta chip + time period selector (tabs: 7d / 30d / 90d)
**Empty states**: Centered illustration placeholder (simple SVG icon in pastel circle) + heading + subtext + primary CTA button
---
## 10. Responsive Design — MANDATORY
Every screen MUST be fully responsive. This is not optional. Build mobile-first.
### Breakpoints
```javascript
/* Mobile first — base styles target mobile */
/* sm  */ @media (min-width: 640px)  { ... }
/* md  */ @media (min-width: 768px)  { ... }
/* lg  */ @media (min-width: 1024px) { ... }
/* xl  */ @media (min-width: 1280px) { ... }

```
### Sidebar Behavior
**Desktop (≥1024px)**: Fixed sidebar, 220px wide, always visible.
**Tablet (768px–1023px)**: Sidebar collapses to 64px icon-only rail. No labels, only icons. Logo shrinks to icon mark only.
**Mobile (<768px)**: Sidebar hidden off-screen. Hamburger menu button in topbar reveals it as a full-width drawer overlay. A dark backdrop overlay sits behind it. Tapping the backdrop closes it.
```javascript
/* Sidebar rail (tablet) */
@media (max-width: 1023px) {
  .sidebar { width: 64px; }
  .sidebar .nav-label,
  .sidebar .nav-item span,
  .sidebar .logo-text,
  .sidebar-footer .user-info { display: none; }
  .nav-item { justify-content: center; padding: 10px; }
}

/* Sidebar drawer (mobile) */
@media (max-width: 767px) {
  .sidebar {
    position: fixed; left: 0; top: 0; height: 100vh;
    width: 260px; z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    box-shadow: none;
  }
  .sidebar.open {
    transform: translateX(0);
    box-shadow: 4px 0 32px rgba(0,0,0,0.15);
  }
  .sidebar .nav-label,
  .sidebar .nav-item span,
  .sidebar .logo-text,
  .sidebar-footer .user-info { display: flex; } /* restore labels in drawer */
  .overlay {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.35); z-index: 199;
  }
  .overlay.show { display: block; }
  .hamburger { display: flex; } /* show hamburger button */
}

```
### Topbar
- Always full-width sticky at top
- On mobile: show hamburger icon (left) + logo (center) + avatar (right)
- On desktop: show breadcrumb (left) + search + actions (right), hamburger hidden
```javascript
.hamburger { display: none; } /* hidden on desktop */
@media (max-width: 767px) {
  .hamburger { display: flex; }
  .topbar-breadcrumb { display: none; }
}

```
### Page Padding
```javascript
.page { padding: 28px; }
@media (max-width: 1023px) { .page { padding: 20px; } }
@media (max-width: 767px)  { .page { padding: 16px; } }

```
### KPI Stat Cards Grid
```javascript
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* desktop: 4 across */
  gap: 16px;
}
@media (max-width: 1023px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); } /* tablet: 2 across */
}
@media (max-width: 480px) {
  .stats-grid { grid-template-columns: 1fr; } /* mobile: stacked */
}

```
### Data Tables on Mobile
Never let tables break the layout. On mobile:
- Wrap table in a `div` with `overflow-x: auto` and `-webkit-overflow-scrolling: touch`
- Add a subtle fade gradient on the right edge to hint at horizontal scroll
- Consider hiding lower-priority columns on mobile with `@media` display:none
- Minimum touch target for action buttons: 44px
```javascript
.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  border-radius: 0 0 14px 14px;
  /* right-edge scroll hint */
  background: linear-gradient(to right, white 80%, rgba(255,255,255,0)) right;
  background-size: 40px 100%;
  background-repeat: no-repeat;
}
@media (max-width: 767px) {
  /* Hide lower priority columns */
  .col-swift, .col-country { display: none; }
  td, th { padding: 12px 10px; font-size: 12.5px; }
}

```
### Cards & Layout Grids
```javascript
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 20px;
}
@media (max-width: 1023px) {
  .dashboard-grid { grid-template-columns: repeat(6, 1fr); }
}
@media (max-width: 767px) {
  .dashboard-grid { grid-template-columns: 1fr; gap: 14px; }
}

```
### Page Header (Title + CTA button)
On mobile the title and CTA button should stack vertically:
```javascript
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
/* Already wraps naturally — no extra media query needed */

```
### Touch Targets
All interactive elements must meet minimum 44x44px touch target on mobile:
```javascript
@media (max-width: 767px) {
  .btn-primary, .btn-ghost { padding: 11px 18px; min-height: 44px; }
  .nav-item { min-height: 44px; }
  td .action-btn { width: 44px; height: 44px; }
}

```
### Modal / Drawer on Mobile
Modals should become bottom sheets on mobile:
```javascript
.modal {
  border-radius: 16px;
  max-width: 520px;
  width: 90%;
}
@media (max-width: 767px) {
  .modal {
    position: fixed; bottom: 0; left: 0; right: 0;
    width: 100%; max-width: 100%;
    border-radius: 20px 20px 0 0;
    max-height: 90vh; overflow-y: auto;
  }
}

```
### Tailwind Responsive Utilities (if using Tailwind)
Use these patterns consistently:
```javascript
// Sidebar
<aside className="hidden lg:flex w-[220px] ...">

// Hamburger
<button className="flex lg:hidden ...">

// Stats grid
<div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">

// Page padding
<main className="p-4 md:p-6 xl:p-8">

// Table wrapper
<div className="overflow-x-auto">
  <table className="min-w-[640px] w-full">

// Hide columns on mobile
<td className="hidden md:table-cell">

```
---
## 11. Anti-Patterns — NEVER DO
- ❌ Dark backgrounds (except for code blocks or optional dark mode)
- ❌ Purple/violet gradients as hero backgrounds
- ❌ Solid bright-colored cards (all cards are white)
- ❌ Inter, Roboto, Arial, system-ui fonts
- ❌ Rounded corners above 16px on cards (too bubbly)
- ❌ Heavy drop shadows (keep shadows subtle)
- ❌ Colored table rows / zebra striping
- ❌ All-caps navigation labels
- ❌ Neon or high-saturation accent colors
- ❌ Cluttered layouts with no breathing room — always maintain generous padding
---
## 12. React / Tailwind Implementation Notes
If using React + Tailwind, map the design tokens like this:
```javascript
// tailwind.config.js additions
colors: {
  brand: {
    primary: '#4F6EF7',
    light: '#EEF1FF',
  },
  surface: '#FFFFFF',
  base: '#F4F5F7',
  border: '#ECEEF2',
  pastel: {
    blue: '#DDE8FF',
    green: '#D6F5E3',
    yellow: '#FFF3D6',
    pink: '#FFE0EC',
    purple: '#EDE0FF',
  }
}

```
Preferred component libraries (in order):
1. **shadcn/ui** — use for tables, dialogs, dropdowns, selects
2. **Radix UI primitives** — for accessible components
3. **Recharts** — for all charts (area, bar, line)
4. **Lucide React** — for all icons
---
## Quick Reference Checklist
Before shipping any screen, verify:
- [ ] All fonts are Plus Jakarta Sans + DM Sans (no fallbacks visible)
- [ ] All backgrounds use `--bg-base` (page) and `--bg-surface` (cards)
- [ ] All status/category labels use pastel chips
- [ ] Cards have `--shadow-card` and `14px` border-radius
- [ ] Spacing follows the 4px grid
- [ ] Hover states exist on all interactive elements
- [ ] Page has staggered fade-up load animation
- [ ] No solid dark backgrounds used anywhere
- [ ] Icons are Lucide, 1.5 stroke width
- [ ] Sidebar collapses to icon rail on tablet, drawer on mobile
- [ ] Hamburger button shown on mobile, hidden on desktop
- [ ] Stat cards grid is 4-col desktop → 2-col tablet → 1-col mobile
- [ ] All tables wrapped in `overflow-x: auto` container
- [ ] Low-priority table columns hidden on mobile
- [ ] Page padding reduces on smaller screens (28px → 20px → 16px)
- [ ] Modals become bottom sheets on mobile
- [ ] All touch targets are minimum 44×44px on mobile