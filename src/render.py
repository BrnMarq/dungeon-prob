"""
Shared sprite cache and fast alpha blitting.

Two things in here, both of them purely about speed - every function
below is pixel-for-pixel equivalent to the straightforward pygame calls
it replaces.

1. blit(). pygame's own per-pixel-alpha blitter has no SIMD path on
   some platforms (arm64 macOS among them), where it runs at a flat
   ~6 Mpx/s no matter the sprite size - a single 480x300 tree costs
   ~23ms there, which is a whole frame's budget on its own.
   pygame.BLEND_ALPHA_SDL2 asks SDL2's own (vectorised) blitter for the
   same "src over dst" composite instead, ~290x faster and verified
   byte-identical on every texture this game ships. Every alpha blit in
   the game should go through here rather than surface.blit directly.

2. sprite()/outline(). Entity render() methods used to rebuild their
   sprite every single frame - allocate an SRCALPHA surface, clear it,
   blit the frame region in, and flip it - and the interactable chests,
   altars and pickups additionally rebuilt their glow outline through
   pygame.mask.from_surface().to_surface() each frame. All of that
   depends only on (texture, frame index, flip/colour), so it is built
   once on first use and cached here.
"""

from typing import Dict, Tuple

import pygame

import settings

# See the module docstring - this is the fast path for anything with an
# alpha channel, and the reason sprites here are convert_alpha()'d
# (SDL2's blitter is fastest when source and destination share the
# display's pixel format).
ALPHA = pygame.BLEND_ALPHA_SDL2


def blit(surface: pygame.Surface, image: pygame.Surface, dest) -> None:
    """Draw image onto surface at dest, compositing through SDL2's
    accelerated alpha blitter rather than pygame's own.
    """
    surface.blit(image, dest, special_flags=ALPHA)


_sprites: Dict[Tuple[str, int, bool], pygame.Surface] = {}


def sprite(texture_id: str, frame_index: int, flipped: bool = False) -> pygame.Surface:
    """
    :param texture_id: A key into settings.TEXTURES/settings.FRAMES.
    :param frame_index: Which of that texture's frames to cut out.
    :param flipped: Whether to mirror the frame horizontally.
    :returns: That frame as a standalone, display-format surface, built
        on first request and cached for every frame after it.
    """
    key = (texture_id, frame_index, flipped)
    image = _sprites.get(key)

    if image is None:
        frame = settings.FRAMES[texture_id][frame_index]
        image = settings.TEXTURES[texture_id].subsurface(frame).convert_alpha()

        if flipped:
            image = pygame.transform.flip(image, True, False)

        _sprites[key] = image

    return image


_outlines: Dict[Tuple[str, int, Tuple[int, ...]], pygame.Surface] = {}


def outline(
    texture_id: str, frame_index: int, color: Tuple[int, ...]
) -> pygame.Surface:
    """
    :param texture_id: A key into settings.TEXTURES/settings.FRAMES.
    :param frame_index: Which of that texture's frames to outline.
    :param color: The solid colour to fill the frame's silhouette with.
    :returns: A silhouette of that frame in color (transparent
        everywhere the frame itself is), for drawing offset behind the
        sprite as a glow - see src.entities.Chest.render.
    """
    key = (texture_id, frame_index, tuple(color))
    image = _outlines.get(key)

    if image is None:
        image = (
            pygame.mask.from_surface(sprite(texture_id, frame_index))
            .to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
            .convert_alpha()
        )
        _outlines[key] = image

    return image


def clear_caches() -> None:
    """Drop every cached sprite/outline - only needed if settings.TEXTURES
    is swapped out at runtime, which nothing currently does.
    """
    _sprites.clear()
    _outlines.clear()
