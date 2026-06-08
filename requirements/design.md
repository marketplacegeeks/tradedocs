# TradeDocs — Design System Reference

**Aesthetic:** LoopAI CRM by Phenomenon Studio — soft-pastel, card-based, premium B2B SaaS.
Calm and organised. White cards floating on a warm gray background. Not dark, not purple-gradient, not neon.

---

## 1. Fonts

Loaded from Google Fonts in `index.css`.

| Role | Font | Use |
|------|------|-----|
| Headings, page titles, KPIs | `Plus Jakarta Sans` | `var(--font-heading)` |
| Body, labels, table text | `DM Sans` | `var(--font-body)` |

**Never use** Inter, Roboto, Arial, or system-ui.

### Type Scale

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Page title | Plus Jakarta Sans | 22px | 700 | `--text-primary` |
| Section heading | Plus Jakarta Sans | 16px | 600 | `--text-primary` |
| Card title | Plus Jakarta Sans | 14px | 600 | `--text-primary` |
| Body / form label | DM Sans | 14px | 400–500 | `--text-secondary` |
| Small label / timestamp | DM Sans | 12px | 500 | `--text-muted` |
| Table header | DM Sans | 11px | 600 | `--text-muted` (uppercase) |
| Chip / badge | DM Sans | 11px | 600 | pastel color |

---

## 2. Color Tokens

All defined as CSS variables in `frontend/src/index.css`.

### Backgrounds

| Variable | Hex | Use |
|----------|-----|-----|
| `--bg-base` | `#F4F5F7` | Main page background |
| `--bg-surface` | `#FFFFFF` | Cards, panels, modals, sidebar |
| `--bg-sidebar` | `#FFFFFF` | Sidebar background |
| `--bg-hover` | `#F0F1F5` | Row hover, nav item hover |
| `--bg-input` | `#F8F9FB` | Input and select backgrounds |

### Primary Action

| Variable | Hex | Use |
|----------|-----|-----|
| `--primary` | `#4F6EF7` | Buttons, active nav, links |
| `--primary-hover` | `#3A58E0` | Button hover state |
| `--primary-light` | `#EEF1FF` | Active nav background, selected rows |

### Text

| Variable | Hex | Use |
|----------|-----|-----|
| `--text-primary` | `#1A1D23` | Headings, bold labels |
| `--text-secondary` | `#5A6070` | Body text, descriptions |
| `--text-muted` | `#9BA3B5` | Timestamps, placeholders |
| `--text-inverse` | `#FFFFFF` | Text on dark/primary backgrounds |

### Borders & Shadows

| Variable | Value | Use |
|----------|-------|-----|
| `--border-light` | `#ECEEF2` | Card borders, dividers |
| `--border-medium` | `#D8DCE6` | Input borders, table lines |
| `--shadow-card` | `0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)` | All cards |
| `--shadow-dropdown` | `0 8px 24px rgba(0,0,0,0.10)` | Dropdowns |
| `--shadow-modal` | `0 16px 48px rgba(0,0,0,0.14)` | Modals and drawers |

### Pastel Chip Colors

Used exclusively for status badges, category labels, and tags. Never solid dark badges.

| Variable pair | Background | Text | Use in TradeDocs |
|---------------|-----------|------|-----------------|
| `--pastel-blue` / `--pastel-blue-text` | `#DDE8FF` | `#3B6FE8` | DRAFT status, avatar initials |
| `--pastel-green` / `--pastel-green-text` | `#D6F5E3` | `#1A8A4A` | APPROVED status |
| `--pastel-yellow` / `--pastel-yellow-text` | `#FFF3D6` | `#B57B00` | PENDING_APPROVAL status |
| `--pastel-pink` / `--pastel-pink-text` | `#FFE0EC` | `#C0335A` | PERMANENTLY_REJECTED status |
| `--pastel-purple` / `--pastel-purple-text` | `#EDE0FF` | `#6B35C2` | General tags |
| `--pastel-orange` / `--pastel-orange-text` | `#FFE8D6` | `#B85C00` | REWORK status |

---

## 3. Document Status → Chip Mapping

Defined in `frontend/src/utils/constants.ts` as `DOCUMENT_STATUS_CHIP`. Always import from there.

```ts
DRAFT                → "chip-blue"
PENDING_APPROVAL     → "chip-yellow"
APPROVED             → "chip-green"
REWORK               → "chip-orange"
PERMANENTLY_REJECTED → "chip-pink"
```

Apply with the global `.chip` class plus the color variant:
```html
<span class="chip chip-green">Approved</span>
```

---

## 4. Layout

### Shell (`AppLayout.tsx`)

```
┌─────────────────────────────────────────────────────┐
│  Sidebar (220px)  │  Top Bar (56px, full width)      │
│  white + border   ├─────────────────────────────────┤
│                   │                                  │
│  Logo             │  Page content                    │
│  Nav items        │  padding: 28px                   │
│                   │  background: --bg-base            │
│  User avatar      │                                  │
└───────────────────┴──────────────────────────────────┘
```

- Sidebar: `width: 220px` (collapses to `64px` icon-rail via the `<` button in the top bar)
- Top bar: `height: 56px`, white, `border-bottom: 1px solid var(--border-light)`
- Content area: `padding: 28px`, `background: var(--bg-base)`, scrollable

### Cards

All content blocks use these exact values:

```css
background: var(--bg-surface);       /* white */
border: 1px solid var(--border-light);
border-radius: 14px;
padding: 20px 24px;
box-shadow: var(--shadow-card);
```

Never use a colored card background. All cards are white.

### Page Header Pattern

Every page opens with a title-left / action-right header:

```
┌────────────────────────────────────────────────┐
│  Page Title (22px, Plus Jakarta Sans 700)       │
│  Subtitle line (optional, muted)                │
│                                          [+ New] │
└────────────────────────────────────────────────┘
```

---

## 5. Navigation

Defined in `AppLayout.tsx` → `NAV_ITEMS`.

| Route | Label | Icon | Roles |
|-------|-------|------|-------|
| `/dashboard` | Dashboard | `LayoutDashboard` | All |
| `/proforma-invoices` | Proforma Invoice | `FileText` | All |
| `/packing-lists` | P.List & C. Invoice | `Package` | All |
| `/purchase-orders` | Purchase Order | `ShoppingBag` | All |
| `/master-data` | Master Data (grouped) | `Database` | Checker, Admin |
| `/users` | User Management | `Users` | Admin |
| `/reports` | Reports | `BarChart2` | Checker, Admin |
| `/training` | Training | `GraduationCap` | All |

Master Data sub-items: Organisations, Banks, T&C Templates, Reference Data.

Active nav item: `background: var(--primary-light)`, `color: var(--primary)`, `font-weight: 600`.

---

## 6. Data Tables

Pattern used on all list pages (PI, PL, PO, etc.).

- Table wrapper: white card (`--bg-surface`, `border-radius: 14px`, `--shadow-card`)
- Header cells: `--bg-base` background, 11px DM Sans 600 uppercase, `--text-muted`
- Row height: ~52px (`padding: 14px 16px`)
- Row hover: `--bg-hover` background
- No zebra striping
- Status column: always a pastel chip, never plain text
- Last column: row-level action links (View, Edit)
- Overflow: wrap in `overflow-x: auto` container

### Status Tabs

Above the table, use a tab strip to filter by status. Example from PI list:

```
All | Draft | Pending Approval | Approved | Rework | Permanently Rejected
```

Active tab: `color: var(--primary)`, `border-bottom: 2px solid var(--primary)`.

---

## 7. Forms

Used on Create and Edit pages (PI, PL, CI, Organisation, Bank, etc.).

- Form sections use white cards with a section title above the fields
- Labels: 13px DM Sans 500, `--text-primary`
- Inputs: `background: var(--bg-input)`, `border: 1px solid var(--border-medium)`, `border-radius: 8px`
- Focus state: `border-color: var(--primary)`, `box-shadow: 0 0 0 2px rgba(79,110,247,0.1)`
- Ant Design form components are overridden in `index.css` to match these tokens

### Line Item Tables (inside forms)

Used on PI (line items + charges), PL (containers → items), CI (aggregated items).

- Inline editable rows within a white card
- Add/remove row controls at the bottom
- Totals row pinned at the bottom with `font-weight: 600`

---

## 8. Buttons

```css
/* Primary — create, save, submit */
background: var(--primary);   /* #4F6EF7 */
color: white;
border-radius: 8px;
padding: 9px 18px;
font-family: var(--font-body);
font-size: 14px;
font-weight: 500;

/* Ghost / Secondary — cancel, back */
background: transparent;
color: var(--text-secondary);
border: 1px solid var(--border-medium);
border-radius: 8px;

/* Danger — reject, delete */
/* Use Ant Design danger variant; follows pink/red */
```

---

## 9. Workflow Action Buttons

Handled by `frontend/src/components/common/WorkflowActionButton.tsx`.

It takes `documentStatus`, `userRole`, and `documentType` as props and renders the correct set of buttons for the current state and role. Do not repeat this logic in individual pages.

| Action | Role | Shown when status |
|--------|------|-------------------|
| Submit for Approval | Maker | DRAFT, REWORK |
| Approve | Checker, Admin | PENDING_APPROVAL |
| Send for Rework | Checker, Admin | PENDING_APPROVAL |
| Permanently Reject | Checker, Admin | PENDING_APPROVAL |

Rework and Permanently Reject require a non-empty comment (enforced by backend too).

---

## 10. Icons

Use **Lucide React** exclusively. Already imported project-wide.

| Context | Size | Stroke width |
|---------|------|--------------|
| Nav items | 18px | 1.5 |
| Inline UI (buttons, labels) | 16px | 1.5 |
| Feature / section icons | 20px | 1.5 |
| Stat card icons | 20px | 1.5 |

Icon color: inherit from parent, or `var(--text-muted)` for decorative icons.
Never use emoji as icons.

---

## 11. Animations

Defined in `index.css`. Use `.card-animate` on cards that load into view.

```css
/* Staggered fade-up on load */
.card-animate { animation: fadeUp 0.3s ease both; }
.card-animate:nth-child(1) { animation-delay: 0.05s; }
.card-animate:nth-child(2) { animation-delay: 0.10s; }
/* ... up to :nth-child(4) */
```

Global hover transition already applied to `*`:
```css
transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
```

---

## 12. Spacing

4px base grid.

| Token | Value | Use |
|-------|-------|-----|
| xs | 4px | Tight gaps, icon padding |
| sm | 8px | Between inline elements |
| md | 16px | Card internal spacing |
| lg | 24px | Between sections |
| xl | 28–32px | Page padding |

---

## 13. Ant Design Overrides

Ant Design is the component library. Global overrides live in `frontend/src/index.css` (lines 169+).
They remap Ant's default tokens to match this design system. Key overrides:

- `.ant-btn-primary` → uses `--primary` and `border-radius: 8px`
- `.ant-card` → `border-radius: 14px`, `--shadow-card`
- `.ant-input`, `.ant-select-selector` → `--bg-input`, `--border-medium`, `border-radius: 8px`
- `.ant-table-thead` → `--bg-base` background, 11px uppercase muted text
- `.ant-table-tbody tr:hover` → `--bg-hover`

When adding new Ant components, check if an override is needed to align with the design system.

---

## 14. Anti-Patterns — Never Do

- Dark backgrounds anywhere in the app
- Purple/violet gradients
- Colored card backgrounds (all cards are white)
- Inter, Roboto, Arial, or system-ui fonts
- Card `border-radius` above 16px
- Heavy drop shadows
- Zebra striping on tables
- All-caps navigation labels
- Neon or high-saturation accent colors
- Hardcoding status strings — always import from `src/utils/constants.ts`
- Calling Axios directly in a component — all API calls go in `src/api/*.ts`

---

## 15. File Locations

| Thing | Location |
|-------|----------|
| CSS variables + global styles | `frontend/src/index.css` |
| Ant Design overrides | `frontend/src/index.css` (line ~169) |
| Status/role constants | `frontend/src/utils/constants.ts` |
| App shell (sidebar + topbar) | `frontend/src/components/AppLayout.tsx` |
| Workflow action buttons | `frontend/src/components/common/WorkflowActionButton.tsx` |
| Audit log drawer | `frontend/src/components/AuditLogDrawer.tsx` |
| API call files | `frontend/src/api/*.ts` |
| Page components | `frontend/src/pages/{section}/` |
