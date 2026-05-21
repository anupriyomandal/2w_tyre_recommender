# CEAT Brand Color System

## Overview
This document defines the official CEAT brand color palette for use across:
- UI / Web / Apps
- Presentations
- Marketing creatives
- Internal tools (AI agents, dashboards, etc.)

Follow these tokens strictly to maintain brand consistency.

---

## 🎨 Primary Brand Colors

### 1. CEAT Blue (Primary)
- Pantone: 286 C  
- CMYK: 96, 73, 0, 0  
- RGB: 0, 85, 170  
- HEX: #0055AA  
- Usage:
  - Primary brand color
  - Headers, CTAs, key highlights
  - Logos and brand-first surfaces

---

### 2. CEAT Orange (Accent)
- Pantone: 151 C  
- CMYK: 0, 65, 100, 0  
- RGB: 245, 130, 69  
- HEX: #F58220  
- Usage:
  - Accent highlights
  - Buttons, alerts, emphasis
  - Call-to-action elements

---

## ⚪ Neutral Colors

### 3. White (Background)
- Pantone: 663 C  
- CMYK: 0, 0, 0, 0  
- RGB: 255, 255, 255  
- HEX: #FFFFFF  
- Usage:
  - Backgrounds
  - Clean layouts
  - Spacing and readability

---

### 4. Dark Blue (Secondary)
- Pantone: 281 C  
- CMYK: 99, 86, 27, 13  
- RGB: 39, 60, 111  
- HEX: #273C6F  
- Usage:
  - Secondary headers
  - Depth backgrounds
  - Corporate / formal layouts

---

### 5. Black (Text / Base)
- Pantone: Neutral Black C  
- CMYK: 0, 0, 0, 100  
- RGB: 0, 0, 0  
- HEX: #000000  
- Usage:
  - Body text
  - High contrast elements
  - Typography

---

## 🧩 Color Roles (Design System)

| Role        | Color        | HEX      | Usage % |
|------------|-------------|----------|--------|
| Primary    | CEAT Blue   | #0055AA  | 60%    |
| Secondary  | Dark Blue   | #273C6F  | 20–30% |
| Accent     | CEAT Orange | #F58220  | 10%    |
| Neutral    | White       | #FFFFFF  | Base   |
| Text/Base  | Black       | #000000  | Text   |

> Follow the **60-30-10 rule** for balanced design wherever possible. :contentReference[oaicite:0]{index=0}

---

## 🧠 Usage Guidelines

### Do:
- Use **CEAT Blue** as dominant identity color
- Use **Orange sparingly** for attention (CTA, highlights)
- Maintain **high contrast** (Blue/White, Black/White)
- Keep layouts clean with **ample white space**

### Don't:
- Overuse Orange (reduces impact)
- Introduce unofficial shades
- Use low-contrast combinations (hurts readability)

---

## 💻 Developer Tokens (Optional)

```json
{
  "primary": "#0055AA",
  "secondary": "#273C6F",
  "accent": "#F58220",
  "white": "#FFFFFF",
  "black": "#000000"
}