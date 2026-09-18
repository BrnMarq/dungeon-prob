"""
Parallax background - src.map.Level owns one (built from its own
get_rect() width) and renders it first each frame, before the tilemap
and entities. A solid sky fill plus four scrolling tree/forest layers,
each lagging the camera by its own BACKGROUND_*_SCROLL_FACTOR (0 = fixed
in place, 1 = scrolls exactly with the world) so farther layers move
less than nearer ones - the classic parallax depth illusion, back to
front: background-forest.png (one wide silhouette) barely scrolls,
huge-trees.png a bit more, tall-trees.png's bare-branch row (its second,
farther) more still, and tall-trees.png's leafy row (its first, closest)
the most.

huge-trees.png/tall-trees.png's cells (800x500, 600x624) are rescaled to
BACKGROUND_*_HEIGHT (aspect-preserved) once at construction, then
scattered as individual tree instances at SPACING intervals (+/- JITTER)
across the level's width plus a viewport's worth of margin on each side
- rather than tiled, since even at these larger sheets stay wider than
this map's own camera scroll range. All three tree layers pin to the top
of the screen (canopies hang down from off-screen above, like an
overhead tree line), unlike background-forest.png's silhouette, which
stays bottom-anchored since its treeline art sits at the bottom of its
own image - and is rescaled to BACKGROUND_FOREST_HEIGHT too (aspect-
preserved), since left at its native 1440x800 the solid ground fill
alone was tall enough to cover the entire (much shorter) viewport,
hiding the treeline silhouette above it.
"""

from typing import Any, List, NamedTuple, Sequence

import random

import pygame

import settings

# tall-trees.png is a 2x2 grid (settings.FRAMES row-major): row 0 (frame
# indices 0-1) is the leafy variant, row 1 (2-3) the bare-branch one -
# split into their own layers (see ParallaxBackground.__init__) instead
# of one layer randomizing across both, per row/tree.
_TALL_TREES_FRONT_ROW_INDICES = (0, 1)
_TALL_TREES_BACK_ROW_INDICES = (2, 3)


class _TreeInstance(NamedTuple):
    x: float
    sprite_index: int


class _Layer(NamedTuple):
    sprites: List[pygame.Surface]
    instances: List[_TreeInstance]
    scroll_factor: float


def _scaled_sprites(
    texture_id: str, frame_indices: Sequence[int], target_height: int
) -> List[pygame.Surface]:
    texture = settings.TEXTURES[texture_id]
    all_frames = settings.FRAMES[texture_id]
    sprites = []
    for index in frame_indices:
        rect = all_frames[index]
        cell = texture.subsurface(rect)
        scale = target_height / rect.height
        target_width = max(1, round(rect.width * scale))
        sprites.append(pygame.transform.smoothscale(cell, (target_width, target_height)))
    return sprites


def _scatter(
    level_width: float, margin: float, spacing: float, jitter: float, sprite_count: int
) -> List[_TreeInstance]:
    instances = []
    x = -margin
    while x <= level_width + margin:
        instances.append(
            _TreeInstance(x + random.uniform(-jitter, jitter), random.randrange(sprite_count))
        )
        x += spacing
    return instances


def _build_layer(
    texture_id: str,
    frame_indices: Sequence[int],
    height: int,
    level_width: float,
    margin: float,
    spacing: float,
    jitter: float,
    scroll_factor: float,
) -> _Layer:
    sprites = _scaled_sprites(texture_id, frame_indices, height)
    instances = _scatter(level_width, margin, spacing, jitter, len(sprites))
    return _Layer(sprites, instances, scroll_factor)


class ParallaxBackground:
    def __init__(self, level_width: float, viewport_width: float) -> None:
        margin = viewport_width

        # Height-only scale (not aspect-preserved, unlike every other
        # layer below) - background-forest.png's 1440px width has to stay
        # exactly as wide as it started, since that width (not this
        # layer's own scroll_factor) is what keeps it covering the
        # viewport as the camera scrolls the level; only its height needs
        # shrinking to fit the screen.
        forest_texture = settings.TEXTURES["background_forest"]
        self._forest_sprite = pygame.transform.scale(
            forest_texture,
            (forest_texture.get_width(), settings.BACKGROUND_FOREST_HEIGHT),
        )

        self._huge_trees = _build_layer(
            "huge_trees",
            range(len(settings.FRAMES["huge_trees"])),
            settings.BACKGROUND_HUGE_TREES_HEIGHT,
            level_width,
            margin,
            settings.BACKGROUND_HUGE_TREES_SPACING,
            settings.BACKGROUND_HUGE_TREES_JITTER,
            settings.BACKGROUND_HUGE_TREES_SCROLL_FACTOR,
        )
        self._tall_trees_back = _build_layer(
            "tall_trees",
            _TALL_TREES_BACK_ROW_INDICES,
            settings.BACKGROUND_TALL_TREES_BACK_HEIGHT,
            level_width,
            margin,
            settings.BACKGROUND_TALL_TREES_BACK_SPACING,
            settings.BACKGROUND_TALL_TREES_BACK_JITTER,
            settings.BACKGROUND_TALL_TREES_BACK_SCROLL_FACTOR,
        )
        self._tall_trees_front = _build_layer(
            "tall_trees",
            _TALL_TREES_FRONT_ROW_INDICES,
            settings.BACKGROUND_TALL_TREES_HEIGHT,
            level_width,
            margin,
            settings.BACKGROUND_TALL_TREES_SPACING,
            settings.BACKGROUND_TALL_TREES_JITTER,
            settings.BACKGROUND_TALL_TREES_SCROLL_FACTOR,
        )

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        surface.fill(settings.BACKGROUND_SKY_COLOR)

        offset_x, _ = camera.offset
        self._render_forest(surface, offset_x)
        self._render_layer(surface, offset_x, self._huge_trees)
        self._render_layer(surface, offset_x, self._tall_trees_back)
        self._render_layer(surface, offset_x, self._tall_trees_front)

    def _render_forest(self, surface: pygame.Surface, offset_x: float) -> None:
        sprite = self._forest_sprite
        screen_x = -offset_x * settings.BACKGROUND_FOREST_SCROLL_FACTOR
        screen_y = surface.get_height() - sprite.get_height()
        surface.blit(sprite, (round(screen_x), round(screen_y)))

    def _render_layer(self, surface: pygame.Surface, offset_x: float, layer: _Layer) -> None:
        surface_width = surface.get_width()

        for instance in layer.instances:
            sprite = layer.sprites[instance.sprite_index]
            screen_x = instance.x - offset_x * layer.scroll_factor
            if screen_x + sprite.get_width() < 0 or screen_x > surface_width:
                continue

            surface.blit(sprite, (round(screen_x), 0))
