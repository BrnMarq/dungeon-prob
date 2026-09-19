import math
from typing import Any, List, TypeVar

import pygame

import settings
from src import render
from src.entities.ShadowExplosion import ShadowExplosion


class ThrownSword:
    """The W ability's projectile (assets/graphics/dark-sword.png),
    spawned by src.entities.player_states.ThrowState. Not an Entity (no
    gravity/tile collision/state machine to it), but conforms to the same
    duck-typed interface src.map.Level's entities list expects
    (update/render/is_dead), like src.entities.DamageNumber.

    Flies in a straight line for settings.SWORD_TRAVEL_DISTANCE, damaging
    each enemy it touches at most once (self._hit_entities) while cycling
    through the thrown/midair/near_max_travel animations by distance
    fraction, then lands and floats in place (sine-tweened y, looping the
    floating animation) until the player touches it - which detonates it
    (area damage plus a src.entities.ShadowExplosion animation at the
    sword's own position) and refunds the player's dash, per the design
    brief.
    """

    TEXTURE_ID = "dark_sword"
    WIDTH = 32
    HEIGHT = 32

    THROWN_FRAMES = [0, 1, 2]
    MIDAIR_FRAMES = [4, 5]
    NEAR_MAX_TRAVEL_FRAMES = [8, 9, 10, 11]
    FLOATING_FRAMES = [12, 13, 14]

    def __init__(
        self,
        x: float,
        y: float,
        direction: int,
        damage: int,
        player: TypeVar("Player"),
        level: TypeVar("Level"),
    ) -> None:
        self.x = x
        self.y = y
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.start_x = x
        self.direction = direction
        self.damage = damage
        self.flipped = direction < 0
        self.player = player
        self.level = level
        self.is_dead = False

        self.floating = False
        self.base_y = y
        self.float_elapsed = 0.0

        self._hit_entities: set = set()
        self._frame_pos = 0
        self._frame_timer = 0.0
        self._phase = "thrown"
        self.frame_index = self.THROWN_FRAMES[0]

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def update(self, dt: float) -> None:
        if self.floating:
            self._update_floating(dt)
            return

        self._update_flight(dt)

    def _update_flight(self, dt: float) -> None:
        distance_traveled = abs(self.x - self.start_x)
        if distance_traveled >= settings.SWORD_TRAVEL_DISTANCE:
            self._land()
            return

        self.x += settings.SWORD_SPEED * self.direction * dt
        self._apply_flight_damage()

        fraction = distance_traveled / settings.SWORD_TRAVEL_DISTANCE
        if fraction < settings.SWORD_THROWN_DISTANCE_FRACTION:
            phase, frames, interval = (
                "thrown",
                self.THROWN_FRAMES,
                settings.SWORD_THROWN_FRAME_INTERVAL,
            )
        elif fraction < settings.SWORD_MIDAIR_DISTANCE_FRACTION:
            phase, frames, interval = (
                "midair",
                self.MIDAIR_FRAMES,
                settings.SWORD_MIDAIR_FRAME_INTERVAL,
            )
        else:
            phase, frames, interval = (
                "near_max_travel",
                self.NEAR_MAX_TRAVEL_FRAMES,
                settings.SWORD_NEAR_MAX_FRAME_INTERVAL,
            )

        if phase != self._phase:
            self._phase = phase
            self._frame_pos = 0
            self._frame_timer = 0.0
        self._advance_frame(frames, interval, dt)

    def _apply_flight_damage(self) -> None:
        hitbox = self.get_collision_rect()
        for other in self._damageable_entities():
            if id(other) in self._hit_entities:
                continue
            if not hitbox.colliderect(other.get_collision_rect()):
                continue

            other.take_damage(self.damage)
            self._hit_entities.add(id(other))
            self.player.maybe_trigger_samurai_burst()
            settings.SOUNDS["shadow_throw_hit"].play()

    def _land(self) -> None:
        self.floating = True
        self.base_y = self.y
        self.float_elapsed = 0.0
        self._frame_pos = 0
        self._frame_timer = 0.0
        self.frame_index = self.FLOATING_FRAMES[0]

    def _update_floating(self, dt: float) -> None:
        self.float_elapsed += dt
        self.y = self.base_y + math.sin(
            self.float_elapsed * settings.SWORD_FLOAT_SPEED
        ) * settings.SWORD_FLOAT_AMPLITUDE
        self._advance_frame(
            self.FLOATING_FRAMES, settings.SWORD_FLOAT_FRAME_INTERVAL, dt
        )

        if self.get_collision_rect().colliderect(self.player.get_collision_rect()):
            settings.SOUNDS["shadow_sword_pickup"].play()
            self._explode()

    def _advance_frame(self, frames: List[int], interval: float, dt: float) -> None:
        self._frame_timer += dt
        if self._frame_timer >= interval:
            self._frame_timer %= interval
            self._frame_pos = (self._frame_pos + 1) % len(frames)
        self.frame_index = frames[self._frame_pos]

    def _damageable_entities(self) -> List[Any]:
        return [
            other
            for other in self.level.entities
            if other is not self.player
            and other is not self
            and hasattr(other, "take_damage")
            and hasattr(other, "get_collision_rect")
        ]

    def _explode(self) -> None:
        self.floating = False
        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2
        radius = settings.SWORD_EXPLOSION_RADIUS
        radius_squared = radius**2

        for other in self._damageable_entities():
            rect = other.get_collision_rect()
            dx = rect.centerx - center_x
            dy = rect.centery - center_y
            if dx * dx + dy * dy <= radius_squared:
                other.take_damage(self.player.get_damage(settings.SWORD_EXPLOSION_DAMAGE))
                self.player.maybe_trigger_samurai_burst()
                settings.SOUNDS["shadow_throw_hit"].play()

        self.player.dash_cooldown_timer = 0.0

        self.level.entities.append(ShadowExplosion(center_x, center_y))
        self.is_dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        image = render.sprite(self.TEXTURE_ID, self.frame_index, self.flipped)

        dest = camera.apply(pygame.Rect(self.x, self.y, self.width, self.height))
        render.blit(surface, image, dest)
