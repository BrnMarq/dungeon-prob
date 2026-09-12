import math
from typing import TypeVar

import pygame

from gale.text import render_text
from gale.ui.progress_bar import ProgressBar
from gale.ui.theme import get_default_theme

import settings

MARGIN = 4
ICON_SIZE = 32
ICON_GAP = 2
NUM_ABILITY_SLOTS = 4

HP_BAR_HEIGHT = 8
XP_BAR_HEIGHT = 4
LEVEL_BADGE_SIZE = 16

HP_COLOR = pygame.Color(90, 200, 90)
XP_COLOR = pygame.Color(90, 160, 230)
COOLDOWN_OVERLAY_COLOR = (40, 40, 40, 170)  # translucent gray
INVINCIBLE_COLOR = pygame.Color(255, 255, 255)
INVINCIBLE_TEXT_COLOR = pygame.Color(20, 20, 20)


class HUD:
    """Bottom-center HUD: level badge, HP bar (with current/max text), XP
    bar, and a row of ability-icon slots above them. Reads player stats
    fresh every render() - no separate update() bookkeeping needed since
    they're plain attributes on Player.
    """

    def __init__(self, player: TypeVar("Player")) -> None:
        self.player = player
        # Placeholder until a real pixel font (assets/fonts/) exists.
        self.font = pygame.font.Font(None, 12)

        bars_width = NUM_ABILITY_SLOTS * ICON_SIZE + (NUM_ABILITY_SLOTS - 1) * ICON_GAP
        block_height = ICON_SIZE + HP_BAR_HEIGHT + XP_BAR_HEIGHT
        block_width = LEVEL_BADGE_SIZE + MARGIN + bars_width

        block_left = (settings.VIRTUAL_WIDTH - block_width) // 2
        self.bars_x = block_left + LEVEL_BADGE_SIZE + MARGIN
        block_top = settings.VIRTUAL_HEIGHT - MARGIN - block_height

        self.icons_y = block_top
        hp_bar_y = self.icons_y + ICON_SIZE
        xp_bar_y = hp_bar_y + HP_BAR_HEIGHT

        self.level_badge_rect = pygame.Rect(
            block_left,
            block_top + (block_height - LEVEL_BADGE_SIZE) // 2,
            LEVEL_BADGE_SIZE,
            LEVEL_BADGE_SIZE,
        )

        self.hp_bar = ProgressBar(
            self.bars_x, hp_bar_y, bars_width, HP_BAR_HEIGHT, color=HP_COLOR
        )
        self.xp_bar = ProgressBar(
            self.bars_x, xp_bar_y, bars_width, XP_BAR_HEIGHT, color=XP_COLOR
        )

        # marze-abilities.png frames are native 32x32 - scaled once here to
        # fill ICON_SIZE slots rather than per-frame in render(). Surface.blit
        # never scales on its own, it always draws at the source's native
        # size positioned at the dest rect's topleft.
        abilities_texture = settings.TEXTURES["marze_abilities"]
        self.icons = [
            pygame.transform.scale(
                abilities_texture.subsurface(frame_rect), (ICON_SIZE, ICON_SIZE)
            )
            for frame_rect in settings.FRAMES["marze_abilities"]
        ]

        # Built once and reused every frame a slot is on cooldown, rather
        # than allocating a fresh translucent surface per slot per render.
        self.cooldown_overlay = pygame.Surface((ICON_SIZE, ICON_SIZE), pygame.SRCALPHA)
        self.cooldown_overlay.fill(COOLDOWN_OVERLAY_COLOR)

    def render(self, surface: pygame.Surface) -> None:
        theme = get_default_theme()
        player = self.player

        self.hp_bar.value = player.hp
        self.hp_bar.max_value = player.max_hp
        self.xp_bar.value = player.xp
        self.xp_bar.max_value = player.xp_to_next_level

        if getattr(player, "is_invincible", False):
            pygame.draw.rect(surface, INVINCIBLE_COLOR, self.hp_bar.rect)
            if theme.border_width > 0:
                pygame.draw.rect(
                    surface, theme.border_color, self.hp_bar.rect, theme.border_width
                )
            render_text(
                surface,
                "INVINCIBLE",
                self.font,
                self.hp_bar.rect.centerx,
                self.hp_bar.rect.centery,
                INVINCIBLE_TEXT_COLOR,
                center=True,
            )
        else:
            self.hp_bar.render(surface)
            render_text(
                surface,
                f"{player.hp}/{player.max_hp}",
                self.font,
                self.hp_bar.rect.centerx,
                self.hp_bar.rect.centery,
                theme.text_color,
                center=True,
                shadowed=True,
            )

        self.xp_bar.render(surface)

        pygame.draw.rect(surface, theme.background_color, self.level_badge_rect)
        pygame.draw.rect(
            surface, theme.border_color, self.level_badge_rect, theme.border_width
        )
        render_text(
            surface,
            str(player.level_num),
            self.font,
            self.level_badge_rect.centerx,
            self.level_badge_rect.centery,
            theme.text_color,
            center=True,
        )

        for i in range(NUM_ABILITY_SLOTS):
            x = self.bars_x + i * (ICON_SIZE + ICON_GAP)
            slot_rect = pygame.Rect(x, self.icons_y, ICON_SIZE, ICON_SIZE)
            surface.blit(self.icons[i], slot_rect)

            remaining, _total = player.get_ability_cooldown(i)
            if remaining > 0:
                surface.blit(self.cooldown_overlay, slot_rect)
                render_text(
                    surface,
                    str(math.ceil(remaining)),
                    self.font,
                    slot_rect.centerx,
                    slot_rect.centery,
                    theme.text_color,
                    center=True,
                    shadowed=True,
                )

            pygame.draw.rect(surface, theme.border_color, slot_rect, theme.border_width)
