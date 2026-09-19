"""
A one-shot explosion animation played where a src.entities.ThrownSword
detonates (see ThrownSword._explode) - assets/graphics/shadow-explosion.
png's 4 frames. Duck-typed the same way as src.entities.HitEffect
(update/render/is_dead) so src.map.Level's entities list needs no
special-casing - plays through its frames once, then marks itself dead,
no looping/respawn.
"""

from typing import Any

import pygame

import settings
from src import render

_FRAME_COUNT = 4


class ShadowExplosion:
    TEXTURE_ID = "shadow_explosion"

    def __init__(self, center_x: float, center_y: float) -> None:
        frame = settings.FRAMES[self.TEXTURE_ID][0]
        self.x = center_x - frame.width / 2
        self.y = center_y - frame.height / 2
        self.is_dead = False

        self._frame_pos = 0
        self._frame_timer = 0.0
        self.frame_index = 0

    def update(self, dt: float) -> None:
        self._frame_timer += dt
        if self._frame_timer < settings.SHADOW_EXPLOSION_FRAME_INTERVAL:
            return

        self._frame_timer -= settings.SHADOW_EXPLOSION_FRAME_INTERVAL
        self._frame_pos += 1
        if self._frame_pos >= _FRAME_COUNT:
            self.is_dead = True
            return

        self.frame_index = self._frame_pos

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        frame = settings.FRAMES[self.TEXTURE_ID][self.frame_index]
        image = render.sprite(self.TEXTURE_ID, self.frame_index)

        dest = camera.apply(pygame.Rect(self.x, self.y, frame.width, frame.height))
        render.blit(surface, image, dest)
