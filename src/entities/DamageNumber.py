from typing import Any

import pygame

from gale.text import render_text

import settings

RISE_SPEED = 20
LIFETIME = 0.8

_font = pygame.font.Font(None, 14)


class DamageNumber:
    """A floating combat-text popup - rises and fades out over LIFETIME
    seconds. Not an Entity (no gravity/collision/state machine to it), but
    conforms to the same duck-typed interface src.map.Level's entities list
    expects (update/render/is_dead), so it drops into Level.entities like
    any other entity with no special-casing in Level's update/render loop.
    """

    def __init__(self, x: float, y: float, amount: int) -> None:
        self.x = x
        self.y = y
        self.amount = amount
        self.age = 0.0
        self.is_dead = False

    def update(self, dt: float) -> None:
        self.age += dt
        self.y -= RISE_SPEED * dt
        if self.age >= LIFETIME:
            self.is_dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        dest = camera.apply(pygame.Rect(self.x, self.y, 0, 0))
        render_text(
            surface,
            str(self.amount),
            _font,
            dest.x,
            dest.y,
            settings.DAMAGE_NUMBER_COLOR,
            center=True,
            shadowed=True,
        )
