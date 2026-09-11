from typing import Any, Tuple

import pygame


def draw_translucent_rect(
    surface: pygame.Surface,
    camera: Any,
    rect: pygame.Rect,
    color: Tuple[int, int, int, int],
) -> None:
    """Draws rect (world-space) as a translucent overlay, camera-transformed.
    pygame.draw.rect ignores alpha on a non-SRCALPHA surface, so this fills
    a small SRCALPHA surface instead and blits it - blit does composite
    alpha correctly.
    """
    screen_rect = camera.apply(rect)
    overlay = pygame.Surface(
        (max(screen_rect.width, 1), max(screen_rect.height, 1)), pygame.SRCALPHA
    )
    overlay.fill(color)
    surface.blit(overlay, screen_rect)
