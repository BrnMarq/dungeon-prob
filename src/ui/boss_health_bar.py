"""
The zone guardian's health bar - one wide bar across the top of the
screen for as long as it is alive, drawn by src.states.PlayState.render
on top of the normal HUD.

Deliberately not the overhead src/ui/health_bar.py bar every other enemy
gets (BossReaper.SHOW_HEALTH_BAR is False for exactly this reason): a
boss fight wants its health readable without looking away from the
player. It is centered and sized (settings.BOSS_BAR_*) to clear the HUD's
own top-left gold counter and top-right run-timer sign.
"""

from typing import Any

import pygame

from gale.text import render_text

import settings

_FONT = pygame.font.Font(None, 14)
_NAME_GAP = 2


def render(surface: pygame.Surface, boss: Any) -> None:
    """Draws the name plate and hp bar for boss. Unlike the overhead
    enemy bar this stays on screen at full health too - it is the fight's
    header, not a "this one is hurt" marker - but it does disappear once
    the guardian starts dying, so the victory beat isn't spent staring at
    an empty bar.
    """
    if boss is None or boss.hp <= 0:
        return

    bar_rect = pygame.Rect(
        (settings.VIRTUAL_WIDTH - settings.BOSS_BAR_WIDTH) // 2,
        settings.BOSS_BAR_TOP,
        settings.BOSS_BAR_WIDTH,
        settings.BOSS_BAR_HEIGHT,
    )

    render_text(
        surface,
        settings.BOSS_NAME.upper(),
        _FONT,
        bar_rect.centerx,
        bar_rect.top - _FONT.get_height() - _NAME_GAP,
        settings.BOSS_BAR_NAME_COLOR,
        center=True,
        shadowed=True,
    )

    # The background is translucent, so it needs its own surface - filling
    # straight onto the display would drop the alpha.
    background = pygame.Surface(bar_rect.size, pygame.SRCALPHA)
    background.fill(settings.BOSS_BAR_BG_COLOR)
    surface.blit(background, bar_rect)

    ratio = 0.0 if boss.max_hp <= 0 else max(0.0, min(1.0, boss.hp / boss.max_hp))
    fill_width = int(bar_rect.width * ratio)
    if fill_width > 0:
        pygame.draw.rect(
            surface,
            settings.BOSS_BAR_FILL_COLOR,
            pygame.Rect(bar_rect.x, bar_rect.y, fill_width, bar_rect.height),
        )

    pygame.draw.rect(surface, settings.BOSS_BAR_BORDER_COLOR, bar_rect, 1)

    render_text(
        surface,
        f"{int(boss.hp)} / {int(boss.max_hp)}",
        _FONT,
        bar_rect.centerx,
        bar_rect.centery - _FONT.get_height() // 2,
        settings.BOSS_BAR_NAME_COLOR,
        center=True,
        shadowed=True,
    )
