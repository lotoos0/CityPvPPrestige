# Building Assets Guide

Please add PNG files for each building type to this folder.

## Required Files

For isometric rendering, each building type needs its own PNG file:

1. `gold_mine.png` - Gold Mine building
2. `house.png` - House building
3. `power_plant.png` - Power Plant building
4. `barracks.png` - Barracks building
5. `wall.png` - Wall building
6. `tower.png` - Tower building
7. `storage.png` - Storage building

## Optional: Level Variants

If you want different graphics for building levels, you can also add:
- `gold_mine_1.png`, `gold_mine_2.png`, `gold_mine_3.png`, etc.
- Same pattern for other buildings

## Recommended Image Specs

For best isometric rendering:
- **Dimensions**: 128x64 pixels (2:1 ratio) or 256x128 (higher quality)
- **Format**: PNG with transparency
- **Style**: Isometric view (45° angle)
- **Anchor point**: Bottom center of the image should be the tile center
- **Background**: Transparent (no background)

## Empty Tile

Optionally add:
- `tile_empty.png` - Base tile texture for empty spaces

Once you add your PNG files here, I'll integrate them into the isometric renderer.
