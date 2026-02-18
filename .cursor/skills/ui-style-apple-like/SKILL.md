---
name: ui-style-apple-like
description: Build app UI with a 3-column layout (L1 Sidebar, L2 List, L3 Content), Apple-like spacing and contrast, and specified colors/typography. Use when implementing or updating layout, sidebar, main content area, or when the user asks for Apple-like UI, 3-column layout, or these style rules.
---

# UI Style: Apple-like 3-Column Layout

Apply these rules when building or updating the app shell, sidebar, and main layout.

## 1. Global Layout & Colors

- **Layout**: 3-column architecture — **L1 Sidebar** (nav), **L2 List** (optional list pane), **L3 Content** (main area).
- **Backgrounds**:
  - Main content (L3): pure white `#FFFFFF`.
  - L1 Sidebar: light neutral gray `#F3F4F6` (Gray 100).
- **Dividers**: 1px border `#E5E7EB` between columns.
- **Typography**: Clean sans-serif — Inter or system UI stack (e.g. `Inter, system-ui, sans-serif`).

## 2. L1 Sidebar (Navigation)

- **Width**: 64px (`w-16`).
- **Background**: `#F3F4F6` (e.g. `bg-[#F3F4F6]` or Tailwind gray-100).
- **Icon styling**:
  - **Default**: Icon color `#6B7280` (Gray 500), transparent background, centered.
  - **Active**: Container background `#FFFFFF`, `shadow-sm`, icon color Primary Green `#00B96B`, container `rounded-xl` (12px).
  - **Hover**: Background `#E5E7EB`, icon color unchanged.
- Use **Lucide-react** for icons. Buttons/links: `transition` with `duration-200`.

## 3. Component Vibe

- **Apple-like**: Spacious, high-contrast, clean. Avoid clutter.
- **Icons**: Lucide-react only.
- **Motion**: Smooth transitions; use `duration-200` (or equivalent) on interactive elements.

## Quick Reference (Tailwind-style)

| Element        | Value                    |
|----------------|--------------------------|
| L3 background  | `#FFFFFF` / white        |
| L1 background  | `#F3F4F6` / gray-100     |
| Divider        | 1px `#E5E7EB`            |
| Sidebar width  | 64px                     |
| Icon default   | `#6B7280` (gray-500)      |
| Icon active    | `#00B96B` (primary green)|
| Active container | white bg, shadow-sm, rounded-xl |
| Hover container| `#E5E7EB` bg             |
