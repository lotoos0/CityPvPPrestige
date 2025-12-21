# Rendering rules (isometric 2.5D)

Goal: keep isometric rendering consistent so new buildings never break layout.

---

## Core standards (must-have)

- Tile size (diamond): 128x64 px (editable only by explicit decision).
- World units: 1 tile = 128x64 px.
- Render order: Y-sort by tile Y (back to front), then X as tie-breaker.
- Anchor point: bottom center of footprint (for 1x1, center of tile base).
- Shadow policy: separate shadow layer, soft and low-opacity.

---

## Anchor math (canonical)

Definitions:
- Tile diamond is 128x64 px.
- Tile origin is the top point of the footprint diamond (0, 0).
- Footprint size is W x H tiles.

Footprint diamond bounds:
- width_px = (W + H) * 64
- height_px = (W + H) * 32

Anchor point (bottom center of footprint):
- anchor_x = width_px / 2
- anchor_y = height_px

Examples:
- 1x1 -> width 128, height 64, anchor [64, 64]
- 2x2 -> width 256, height 128, anchor [128, 128]
- 3x2 -> width 320, height 160, anchor [160, 160]

Notes:
- All sprites must align their base to this anchor.
- Any per-building offset must be declared in metadata.

---

## Practical notes

- Sprite PNGs include no baked shadow unless explicitly approved.
- All buildings must use the same anchor convention.
- Any change to tile size requires art re-export.
