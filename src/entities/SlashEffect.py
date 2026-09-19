"""
A one-shot slash sprite played over one of the zone guardian's swings
(src.entities.boss_states.SwipeState/LongSlashState) - assets/graphics/
boss/slash-effect-norm.png for the scythe swipe, slash-effect-wide.png
for the long sweep.

Purely cosmetic: the damage those attacks deal comes from src.entities.
BossReaper.attack_hitbox_rect, not from this. Duck-typed the same way as
src.entities.HitEffect/ShadowExplosion (update/render/is_dead) so
src.map.Level's entities list needs no special-casing - plays through its
frames once, mirrored to match the swing's direction, then marks itself
dead.
"""

from typing import Any

import pygame

import settings
from src import render


class SlashEffect:
    def __init__(
        self,
        texture_id: str,
        center_x: float,
        center_y: float,
        frame_interval: float,
        flipped: bool = False,
    ) -> None:
        self.texture_id = texture_id
        self.frame_interval = frame_interval
        self.flipped = flipped
        self._frame_count = len(settings.FRAMES[texture_id])

        frame = settings.FRAMES[texture_id][0]
        self.x = center_x - frame.width / 2
        self.y = center_y - frame.height / 2
        self.is_dead = False

        self._frame_timer = 0.0
        self.frame_index = 0

    def update(self, dt: float) -> None:
        self._frame_timer += dt
        if self._frame_timer < self.frame_interval:
            return

        self._frame_timer -= self.frame_interval
        self.frame_index += 1
        if self.frame_index >= self._frame_count:
            self.frame_index = self._frame_count - 1
            self.is_dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        frame = settings.FRAMES[self.texture_id][self.frame_index]
        image = render.sprite(self.texture_id, self.frame_index, self.flipped)

        dest = camera.apply(pygame.Rect(self.x, self.y, frame.width, frame.height))
        render.blit(surface, image, dest)
