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


def draw_translucent_circle(
    surface: pygame.Surface,
    camera: Any,
    center: Tuple[float, float],
    radius: float,
    color: Tuple[int, int, int, int],
) -> None:
    """Draws a world-space circle (center/radius) as a translucent overlay,
    camera-transformed - same SRCALPHA-overlay trick as draw_translucent_rect,
    sized to the circle's bounding box and filled with pygame.draw.ellipse
    rather than surface.fill so only the disc (not the whole box) is tinted.
    """
    bounds = camera.apply(
        pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
    )
    overlay = pygame.Surface(
        (max(bounds.width, 1), max(bounds.height, 1)), pygame.SRCALPHA
    )
    pygame.draw.ellipse(overlay, color, overlay.get_rect())
    surface.blit(overlay, bounds)
