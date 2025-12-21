# Art Direction - Corporate Cyberpunk (FoE-inspired)

The game uses a corporate cyberpunk aesthetic inspired by the structural clarity of Forge of Empires.

Key principles:
- City as a strategic grid, not a living world.
- Buildings represent functions, not realism.
- Clean, ordered, system-driven cyberpunk.
- Neutral base colors with minimal neon accents.
- Height and mass communicate progression.
- No street-level chaos, crowds, or narrative clutter.

The city represents power, control, and infrastructure - not rebellion or street culture.

---

## Translation notes (FoE -> Corporate Cyberpunk)

1) City as a board, not a world
- Corporate grid, districts as infrastructure modules.
- No street life. No micro-scale storytelling.

2) Clear building hierarchy
- Each building has a distinct silhouette and height.
- Function is readable in under a second.

3) Height equals progression
- Level 1: low, industrial, raw.
- Level 2: more lights, antennas, screens.
- Level 3: dominant tower, corporate prestige.

4) Neutral palette + controlled accents
- Base: steel, concrete, graphite.
- Accents: one system color (cyan or magenta).
- Avoid RGB chaos.

5) No narrative grime
- No crowds, no street trash, no rebellion vibe.
- Cyberpunk of power, not cyberpunk of the streets.

---

## Building names (MVP -> Corporate Cyberpunk)

| MVP building | Cyberpunk name (working) |
| --- | --- |
| Town Hall | Central Command Core |
| House | Habitat Block |
| Mint | Credit Forge |
| Barracks | Security Complex |
| Wall | Perimeter Shield Wall |
| Storage | Vault Depot |
| Scout Tower | Surveillance Spire |

Notes:
- If "Gold Mine" appears in data docs, use "Credit Extractor".
- If "Power Plant" appears in data docs, use "Grid Reactor".
- If "Tower" appears in data docs, use "Defense Spire".

---

## Short UI labels (1-2 words)

| Cyberpunk name | UI label |
| --- | --- |
| Central Command Core | Command |
| Habitat Block | Habitat |
| Credit Forge | Credit |
| Security Complex | Security |
| Perimeter Shield Wall | Shield |
| Vault Depot | Vault |
| Surveillance Spire | Scan |
| Credit Extractor | Extract |
| Grid Reactor | Reactor |
| Defense Spire | Spire |

---

## Color palette (5-6 colors)

Base:
- Graphite: #1E2226
- Steel: #3A4148
- Concrete: #5A626B
- Fog: #C9D1D6

Accent (system color):
- Cyan: #35E0E0
- Magenta: #E04DB0 (optional secondary accent)

Rules:
- Use one accent color per screen; avoid mixing cyan + magenta unless needed.
- Keep base colors dominant (70%+ of the UI/city).

---

## Master prompt (isometric building sprites)

Use this as a base prompt for any building sprite:

```
Isometric 2.5D building sprite for a corporate cyberpunk city builder, PNG with transparent background, Forge of Empires-inspired clarity, clean structured silhouette, no street-level chaos, no people, no vehicles, no graffiti. Neutral base materials (steel, concrete, graphite) with minimal neon accent (cyan OR magenta, not both). Clear functional read at a glance. Soft ground shadow. Consistent scale and anchor point for grid placement. High detail but clean, not noisy.
```

Add per-building modifiers:
- Function tag: "Habitat Block" / "Security Complex" / "Credit Forge" / etc.
- Level tag: "Level 1 low industrial", "Level 2 more lights and antennas", "Level 3 dominant corporate tower".
- Accent choice: "cyan accent" or "magenta accent".

---

## Do not copy from FoE

- Historical ornamentation.
- Soft, fairy-tale shapes.
- Decoration over readability.
- "Pretty" over functional clarity.
