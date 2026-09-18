from typing import Any

import pygame

RISE_SPEED = 10
HOLD_DURATION = 0.4  # seconds shown at full opacity before fading starts
FADE_DURATION = 1.6  # seconds the slow fade-out itself takes
LIFETIME = HOLD_DURATION + FADE_DURATION

_font = pygame.font.Font(None, 14)


class ItemPopup:
    """A floating item-name popup, spawned where src.items.Pickup.update
    collects an item - same duck-typed interface (update/render/is_dead)
    as src.entities.DamageNumber, so it drops into src.map.Level.entities
    like any other entity, but holds at full opacity for HOLD_DURATION
    before fading its alpha out over FADE_DURATION rather than just
    disappearing once its (much shorter) LIFETIME runs out like
    DamageNumber does - render_text (gale.text) has no alpha parameter,
    so the text is rendered to its own surface here and faded with
    Surface.set_alpha instead of going through it.
    """

    def __init__(self, x: float, y: float, text: str, color: pygame.Color) -> None:
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.age = 0.0
        self.is_dead = False

    def update(self, dt: float) -> None:
        self.age += dt
        self.y -= RISE_SPEED * dt
        if self.age >= LIFETIME:
            self.is_dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        dest = camera.apply(pygame.Rect(self.x, self.y, 0, 0))

        alpha = 255
        if self.age > HOLD_DURATION:
            fade_progress = (self.age - HOLD_DURATION) / FADE_DURATION
            alpha = round(255 * (1 - min(1.0, fade_progress)))

        shadow = _font.render(self.text, True, (0, 0, 0))
        shadow.set_alpha(alpha)
        shadow_rect = shadow.get_rect(center=(dest.x + 1, dest.y + 1))
        surface.blit(shadow, shadow_rect)

        text_image = _font.render(self.text, True, self.color)
        text_image.set_alpha(alpha)
        text_rect = text_image.get_rect(center=(dest.x, dest.y))
        surface.blit(text_image, text_rect)
