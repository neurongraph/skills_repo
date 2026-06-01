---
name: pptx-surjit
description: "Use this skill any time you need to create or edit a .pptx presentation for Surjit. This skill enforces the IBM Plex design language — typography-forward, flat geometry, sharp corners, restrained color. Trigger whenever the user asks for a deck, slides, or presentation, or references a .pptx file, and especially when they want slides that feel clean, modern, or 'IBM-style'. If the user just says 'make me a deck' or 'build slides', use this skill — it overrides the generic pptx skill for this user."
---

# pptx-surjit

Presentations for Surjit follow the **IBM Plex design language**: typography is the primary design element, shapes are flat and rectangular, and decoration is used only when it carries meaning.

Read [references/pptxgenjs.md](references/pptxgenjs.md) for the technical API reference.

---

## The Design Language

This is a restrained, precision-driven system. Every decision should feel considered, not embellished.

### Typography

**Font**: IBM Plex Sans at all weights. Use Light (weight 300) for titles and headlines. Use Regular for body copy. Use Mono for code or data.

If IBM Plex Sans is not available in the environment, substitute **Calibri Light** for headers and **Calibri** for body — never Arial, never Trebuchet.

**Size scale** — follow this hierarchy strictly:
| Role | Size |
|------|------|
| Cover/impact title | 68–132pt |
| Section headline | 42–68pt |
| Content title | 28–36pt |
| Body / bullets | 16–20pt |
| Captions / metadata | 12–14pt |

**Case**: Always sentence case. Never title case or ALL CAPS for body text. Short standalone labels (e.g. "IBM", acronyms) may use uppercase.

**Line spacing**: 1.0–1.1× for headlines. 1.2–1.4× for body text. Tight is intentional.

**Alignment**: Left-align everything. Center only when text is deliberately isolated as a visual statement (rare).

---

### Color Palette

The IBM Plex palette. Use colors as flat, solid fills only — no gradients, no opacity blends for decorative effect.

| Name | Hex | Use |
|------|-----|-----|
| **Black** | `161616` | Primary text, dark backgrounds |
| **White** | `FFFFFF` | Text on dark, light backgrounds |
| **Cool Gray 10** | `F4F4F4` | Default slide background |
| **Cool Gray 20** | `E0E0E0` | Subtle dividers, secondary containers |
| **Cool Gray 60** | `8D8D8D` | Captions, metadata, secondary labels |
| **Blue 60** | `0F62FE` | Primary accent — use sparingly |
| **Purple 50** | `A56EFF` | Alternate accent |
| **Teal 50** | `009D9A` | Data/science accent |
| **Magenta 60** | `9F1853` | Emphasis, contrast |
| **Red 50** | `FA4D56` | Warnings, high-emphasis callouts |

**Background strategy**: Default to `F4F4F4` (Cool Gray 10) for content slides. Use `161616` (Black) for impact/cover slides. Use `FFFFFF` sparingly for high-contrast content need. Never use a colored background for a regular content slide.

**Color discipline**: One accent color per presentation (pick from the palette above). Use it for 1–2 elements per slide max. If in doubt, add no color — black and gray are sufficient.

---

### Shape Language

**Sharp corners only.** Every rectangle, container, or dividing element must have `0` corner radius. This is non-negotiable — it defines the IBM aesthetic.

**Thin lines over thick shapes.** Use 1pt (`w: 0.01"`) hairlines as dividers. A thin horizontal rule at y=0.9" separating the title from the body is a valid structural element.

**Small rectangular nodes** (e.g., a 0.15"×0.15" solid square in an accent color) can be used as micro-accents near a title or section marker. Use at most one per slide.

**No decorative shapes.** Every shape on a slide must serve a structural or informational purpose. Shapes placed purely for visual "energy" don't belong here.

---

### Slide Backgrounds

```javascript
// Default content slide — Cool Gray 10
slide.background = { color: "F4F4F4" };

// Impact/cover/section divider — Black
slide.background = { color: "161616" };

// When black background: flip text to white
// color: "FFFFFF" on title, "8D8D8D" on metadata
```

---

### Layout Patterns

Pick one of these per slide. Don't mix multiple patterns on one slide.

**1. Full-bleed type** (cover, section titles, impact statements)
- Title fills 70–80% of the slide height at 68–132pt
- No other content, or a single subtitle line at 28pt below
- Background: black or Cool Gray 10

**2. Headline + body** (most content slides)
- Title at top-left, 28–36pt, Light weight
- Optional thin hairline rule below title (y = title_bottom + 0.1")
- Body content begins 0.2" below the rule
- Left margin: 0.6". Right margin: 0.6".

**3. Two-column split** (comparisons, quote + context)
- Left column: 4.5" wide, headline or large quote
- Right column: 4.5" wide, body or supporting content
- 0.3" gutter between columns
- Columns start at x=0.6" and x=5.4"

**4. Stat/callout grid** (metrics, key numbers)
- 2×2 or 3×1 flat rectangular containers
- Sharp corners, no shadow, thin 1pt border in `E0E0E0`
- Large number (48–60pt) at top of container, label below in 14pt

**5. Horizontal stepped list** (process flows, steps)
- 3–5 items left to right
- Each item: small number label (Blue 60, 14pt bold) above short text
- A thin 1pt line in `E0E0E0` connects them horizontally

---

### Forbidden Elements

These patterns are **never** acceptable in this design system:

- **Colored sidebars** — vertical bars of color along the left or right edge
- **Edge accent rectangles** — decorative rectangles hugging slide borders
- **Floating rounded cards** — content containers with rounded corners or drop shadows
- **Corporate blue gradients** — any gradient involving blue tones, "sky-to-navy", etc.
- **Gradient fills of any kind** on visible design elements
- **Accent lines under titles** — horizontal rules immediately under title text as decoration
- **Dark blue backgrounds used generically** — dark backgrounds are for black only, not navy/dark-blue
- **Icon circles** — icons placed inside colored circles
- **All-caps body text** — headlines may use caps only as a rare deliberate choice
- **Multiple accent colors** on the same slide

---

### Typography in Code

```javascript
// Cover title — IBM Plex Sans Light, black on light or white on dark
slide.addText("Title text here", {
  x: 0.6, y: 0.8, w: 8.8, h: 3.5,
  fontFace: "IBM Plex Sans Light",
  fontSize: 84,
  color: "161616",       // or "FFFFFF" on dark background
  bold: false,
  align: "left",
  valign: "top",
  margin: 0,
});

// Content slide title — smaller, same weight
slide.addText("Section title", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.7,
  fontFace: "IBM Plex Sans Light",
  fontSize: 28,
  color: "161616",
  bold: false,
  align: "left",
  margin: 0,
});

// Hairline rule under title
slide.addShape(pres.ShapeType.rect, {
  x: 0.6, y: 1.15, w: 8.8, h: 0.01,
  fill: { color: "E0E0E0" },
  line: { color: "E0E0E0", width: 0 },
});

// Body text
slide.addText("Body content", {
  x: 0.6, y: 1.4, w: 8.8, h: 3.5,
  fontFace: "IBM Plex Sans",
  fontSize: 18,
  color: "161616",
  align: "left",
  valign: "top",
  lineSpacingMultiple: 1.3,
});

// Micro-accent node (optional, max one per slide)
slide.addShape(pres.ShapeType.rect, {
  x: 0.6, y: 0.38, w: 0.12, h: 0.12,
  fill: { color: "0F62FE" },
  line: { color: "0F62FE", width: 0 },
});

// Caption / metadata
slide.addText("Source: IBM", {
  x: 0.6, y: 5.3, w: 8.8, h: 0.2,
  fontFace: "IBM Plex Sans",
  fontSize: 12,
  color: "8D8D8D",
  align: "left",
  margin: 0,
});
```

---

### Slide Structure Template

Every slide should follow this spatial skeleton:

```
y=0.4"  ┌─ Title (28–36pt, IBM Plex Sans Light) ────────────────────┐
y=1.15" ├─ Thin rule (1pt, E0E0E0) ──────────────────────────────────┤
y=1.3"  │                                                             │
        │  Content area                                               │
        │                                                             │
y=5.1"  ├─ Footer rule (optional, 1pt, E0E0E0) ──────────────────────┤
y=5.25" └─ Caption / source (12pt, 8D8D8D)          Slide number ───┘
```

Left margin: `x=0.6"`. Right edge: `x=9.4"` (for 10" wide slide). Content width: `w=8.8"`.

---

## Workflow

### Creating from Scratch

Use pptxgenjs. Follow the design rules above for every element.

```bash
npm install -g pptxgenjs
node generate.js
```

Read [references/pptxgenjs.md](references/pptxgenjs.md) for full API reference.

### Editing an Existing Deck

When working from the IBM template (`.potx` file at `/Users/surjitdas/Library/CloudStorage/OneDrive-Personal/Landing/IBM_presentation_template_v_2_0_Plex.potx`):

1. Extract and inspect: `python -m markitdown presentation.pptx`
2. Unpack the XML: `python scripts/office/unpack.py presentation.pptx unpacked/`
3. Edit slide XML directly, then repack
4. Run visual QA (see below)

---

## QA

Visual bugs are common. Treat first render as broken until proven otherwise.

### Content check
```bash
python -m markitdown output.pptx
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|placeholder"
```

### Convert to images for visual review
```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

### Visual inspection checklist (use a subagent with fresh eyes)
- No element has rounded corners
- No gradient fills visible
- No colored sidebars or edge rectangles
- Font is IBM Plex Sans (or Calibri Light as fallback)
- All titles are sentence case
- Left alignment consistent across slides
- Sufficient margin from edges (≥0.5" / 0.6" preferred)
- Text not overflowing or clipped
- Background is only `F4F4F4`, `161616`, or `FFFFFF`
- Accent color used ≤2 times per slide

### Fix loop
1. Generate → convert → inspect
2. List every issue found (if zero found, look again)
3. Fix → re-render affected slides
4. Repeat until clean pass

---

## Dependencies

- `pip install "markitdown[pptx]"` — text extraction
- `npm install -g pptxgenjs` — create from scratch
- LibreOffice (`soffice`) — PDF conversion (use `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) — PDF to images
