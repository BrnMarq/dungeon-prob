"""
A static, non-interactive sprite dropped onto the level purely for set
dressing - no collision, no interaction, and update() is a permanent
no-op. Duck-typed like every other Level entity (update/render/is_dead)
so src.map.Level needs no special-casing for it, and is_dead never
flips true, so it lives for the whole level.

Currently used for the two ruins-pillars.png columns
src.states.PlayState._spawn_pillars plants on either side of the
player's spawn point - frame 0 on the left, frame 1 on the right, the
right one passed flipped=True for a mirrored, symmetric pair.
"""

from typing import Any

import pygame

import settings
from src import render


class Decoration:
    def __init__(
        self,
        x: float,
        y: float,
        texture_id: str,
        frame_index: int = 0,
        flipped: bool = False,
    ) -> None:
        self.x = x
        self.y = y
        frame_rect = settings.FRAMES[texture_id][frame_index]
        self.width = frame_rect.width
        self.height = frame_rect.height
        self.texture_id = texture_id
        self.frame_index = frame_index
        self.flipped = flipped
        self.is_dead = False

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        image = render.sprite(self.texture_id, self.frame_index, self.flipped)
        dest = camera.apply(pygame.Rect(self.x, self.y, self.width, self.height))
        render.blit(surface, image, dest)
