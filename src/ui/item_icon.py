"""
Shared builder for a collected item's icon - the 16x16 art from
white-items.png/red-items.png composited with the rarity-colored 1px
outline src.items.Pickup draws in the world, so an item looks the same
everywhere it is listed.

Used by src.states.VictoryState's end-of-run summary and by src.ui.HUD's
item bar. It lives here rather than in either of them because ui/
importing from states/ would be backwards, and because the two showing
the same item differently would be a bug in itself.
"""

from typing import Dict, Tuple

import pygame

import settings
from src import render

# Native item art is 16x16 - composited with its outline onto an 18x18
# canvas (1px of room on every side for the outline to occupy), then
# scaled up as one piece so the outline scales with the icon instead of
# staying a flat 1px sliver next to a much bigger icon.
NATIVE_SIZE = 16
_OUTLINE_OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1))

_cache: Dict[Tuple[str, int, float], pygame.Surface] = {}


def size_for(scale: float) -> int:
    """
    :returns: The side length build() returns at this scale - so callers
        can lay out a row of icons without building them first.
    """
    return round((NATIVE_SIZE + 2) * scale)


def build(texture_id: str, frame_index: int, scale: float) -> pygame.Surface:
    """
    :param texture_id: "items" or "red_items" (see src.items.definitions).
    :param frame_index: Which icon in that sheet.
    :param scale: Multiplier on the 18x18 composite.
    :returns: That icon with its outline, built once per
        (texture, frame, scale) and cached for every request after.
    """
    key = (texture_id, frame_index, scale)
    icon = _cache.get(key)
    if icon is not None:
        return icon

    canvas_size = NATIVE_SIZE + 2
    canvas = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)

    image = render.sprite(texture_id, frame_index)
    outline_color = settings.ITEM_OUTLINE_COLORS[texture_id]
    outline = render.outline(texture_id, frame_index, outline_color)
    for dx, dy in _OUTLINE_OFFSETS:
        canvas.blit(outline, (1 + dx, 1 + dy))
    canvas.blit(image, (1, 1))

    display_size = size_for(scale)
    icon = pygame.transform.scale(canvas, (display_size, display_size))
    _cache[key] = icon
    return icon
