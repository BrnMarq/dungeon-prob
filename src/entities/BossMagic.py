"""
The zone guardian's ranged attack (src.entities.boss_states.MagicState) -
a delayed detonation centered on wherever the player was standing when
the cast animation finished.

Two phases, so the attack is dodgeable rather than a guaranteed hit:

- "telegraph": for settings.BOSS_MAGIC_TELEGRAPH seconds, nothing but a
  ring drawn on the ground, growing from nothing to BOSS_MAGIC_RADIUS.
  This is the player's window to walk out of it.
- "burst": assets/graphics/shadow-explosion.png's 4 frames (reused from
  src.entities.ShadowExplosion rather than a sheet of its own), with the
  damage applied exactly once, on the frame the burst starts, to the
  target if it is still within BOSS_MAGIC_RADIUS of the center.

Duck-typed like src.entities.HitEffect (update/render/is_dead) so
src.map.Level's entities list needs no special-casing.
"""

import math
from typing import Any, TypeVar

import pygame

import settings
from src import render

_BURST_TEXTURE_ID = "shadow_explosion"
_BURST_FRAME_COUNT = 4
_RING_WIDTH = 1


class BossMagic:
    def __init__(
        self,
        center_x: float,
        center_y: float,
        damage: int,
        target: TypeVar("Player"),
    ) -> None:
        self.center_x = center_x
        self.center_y = center_y
        self.damage = damage
        self.target = target
        self.is_dead = False

        self._telegraph_timer = 0.0
        self._bursting = False
        self._burst_timer = 0.0
        self._frame_index = 0

    def _detonate(self) -> None:
        """Applies the damage once, to a target still inside the ring the
        telegraph drew - checked at this moment rather than when the
        attack was cast, which is what makes walking out of it work.
        """
        if self.target is None or not hasattr(self.target, "take_damage"):
            return

        rect = self.target.get_collision_rect()
        distance = math.hypot(
            self.center_x - rect.centerx, self.center_y - rect.centery
        )
        if distance <= settings.BOSS_MAGIC_RADIUS:
            self.target.take_damage(self.damage)

    def update(self, dt: float) -> None:
        if not self._bursting:
            self._telegraph_timer += dt
            if self._telegraph_timer < settings.BOSS_MAGIC_TELEGRAPH:
                return
            self._bursting = True
            self._burst_timer = 0.0
            self._frame_index = 0
            settings.SOUNDS["rage_hit"].play()
            self._detonate()
            return

        self._burst_timer += dt
        if self._burst_timer < settings.SHADOW_EXPLOSION_FRAME_INTERVAL:
            return

        self._burst_timer -= settings.SHADOW_EXPLOSION_FRAME_INTERVAL
        self._frame_index += 1
        if self._frame_index >= _BURST_FRAME_COUNT:
            self.is_dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        if not self._bursting:
            self._render_telegraph(surface, camera)
            return

        frame = settings.FRAMES[_BURST_TEXTURE_ID][self._frame_index]
        image = render.sprite(_BURST_TEXTURE_ID, self._frame_index)
        dest = camera.apply(
            pygame.Rect(
                self.center_x - frame.width / 2,
                self.center_y - frame.height / 2,
                frame.width,
                frame.height,
            )
        )
        render.blit(surface, image, dest)

    def _render_telegraph(self, surface: pygame.Surface, camera: Any) -> None:
        """The growing ring - drawn rather than animated from a sheet,
        since its whole job is to show the exact radius BOSS_MAGIC_RADIUS
        will be checked against and how much of the delay is left.
        """
        progress = min(
            1.0, self._telegraph_timer / settings.BOSS_MAGIC_TELEGRAPH
        )
        radius = max(1, round(settings.BOSS_MAGIC_RADIUS * progress))

        # camera.apply works in rects, so the center is transformed by
        # asking it for a 1x1 rect at that point.
        dest = camera.apply(pygame.Rect(self.center_x, self.center_y, 1, 1))
        pygame.draw.circle(
            surface,
            settings.BOSS_MAGIC_RING_COLOR,
            (dest.x, dest.y),
            radius,
            _RING_WIDTH,
        )
