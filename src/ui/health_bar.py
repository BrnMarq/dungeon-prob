from typing import Any

import pygame

import settings


def render_health_bar(surface: pygame.Surface, camera: Any, entity: Any) -> None:
    """Overhead hp/max_hp bar for entity, camera-transformed - only drawn
    while entity.hp < entity.max_hp (see settings.ENEMY_HEALTH_BAR_* for
    sizing/colors). Caller (src.map.Level.render) is expected to only call
    this for entities opting in via SHOW_HEALTH_BAR = True.
    """
    if entity.hp >= entity.max_hp:
        return

    hurtbox = entity.get_collision_rect()
    width = settings.ENEMY_HEALTH_BAR_WIDTH
    height = settings.ENEMY_HEALTH_BAR_HEIGHT
    world_rect = pygame.Rect(
        hurtbox.centerx - width / 2,
        hurtbox.top - settings.ENEMY_HEALTH_BAR_OFFSET_Y - height,
        width,
        height,
    )
    screen_rect = camera.apply(world_rect)

    pygame.draw.rect(surface, settings.ENEMY_HEALTH_BAR_BG_COLOR, screen_rect)

    ratio = 0.0 if entity.max_hp <= 0 else max(0.0, min(1.0, entity.hp / entity.max_hp))
    fill_width = int(screen_rect.width * ratio)
    if fill_width > 0:
        pygame.draw.rect(
            surface,
            settings.ENEMY_HEALTH_BAR_FILL_COLOR,
            pygame.Rect(screen_rect.x, screen_rect.y, fill_width, screen_rect.height),
        )

    pygame.draw.rect(surface, settings.ENEMY_HEALTH_BAR_BORDER_COLOR, screen_rect, 1)
