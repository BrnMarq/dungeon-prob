"""
A one-shot slash animation played over an enemy hit by the rage/samurai
sword AOE bursts (src.entities.player_states.RageState._land_hit,
src.entities.Player.maybe_trigger_samurai_burst) - assets/graphics/
blade-effects.png's first row (4 frames; the sheet's other two rows are
unused for now). Duck-typed the same way as src.entities.DamageNumber
(update/render/is_dead) so src.map.Level's entities list needs no
special-casing - plays through its 4 frames once, then marks itself dead,
no looping/respawn.
"""

from typing import Any

import pygame

import settings
from src import render

_FRAME_INDICES = (0, 1, 2, 3)


class HitEffect:
    TEXTURE_ID = "blade_effects"

    def __init__(self, center_x: float, center_y: float) -> None:
        frame = settings.FRAMES[self.TEXTURE_ID][_FRAME_INDICES[0]]
        self.x = center_x - frame.width / 2
        self.y = center_y - frame.height / 2
        self.is_dead = False

        self._frame_pos = 0
        self._frame_timer = 0.0
        self.frame_index = _FRAME_INDICES[0]

    @classmethod
    def spawn_on(cls, level: Any, target: Any) -> None:
        """Appends a new instance to level.entities, centered on target's
        get_collision_rect() - the shared spawn point for both trigger
        sites above.
        """
        rect = target.get_collision_rect()
        level.entities.append(cls(rect.centerx, rect.centery))

    def update(self, dt: float) -> None:
        self._frame_timer += dt
        if self._frame_timer < settings.HIT_EFFECT_FRAME_INTERVAL:
            return

        self._frame_timer -= settings.HIT_EFFECT_FRAME_INTERVAL
        self._frame_pos += 1
        if self._frame_pos >= len(_FRAME_INDICES):
            self.is_dead = True
            return

        self.frame_index = _FRAME_INDICES[self._frame_pos]

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        frame = settings.FRAMES[self.TEXTURE_ID][self.frame_index]
        image = render.sprite(self.TEXTURE_ID, self.frame_index)

        dest = camera.apply(pygame.Rect(self.x, self.y, frame.width, frame.height))
        render.blit(surface, image, dest)
