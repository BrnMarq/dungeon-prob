from typing import Any, Dict, List, Tuple, TypeVar

import pygame

from gale.input_handler import InputData
from gale.text import render_text

import settings
from src import render
from src.audio import play_music
from src.items.definitions import ITEMS
from src.states.BaseState import BaseState

TITLE_FONT_SIZE = 48
STAT_FONT_SIZE = 16
SMALL_FONT_SIZE = 12
PROMPT_FONT_SIZE = 16

TITLE_Y = 36
TIME_Y = 84
KILLS_Y = 128
GOLD_Y = 172
DAMAGE_Y = 200
ITEMS_LABEL_Y = 226
ITEMS_ROW_Y = 250
PROMPT_Y = 336

BACKGROUND_COLOR = pygame.Color(10, 20, 12)
TITLE_COLOR = pygame.Color(255, 215, 90)
STAT_COLOR = pygame.Color(235, 235, 235)
PROMPT_COLOR = pygame.Color(235, 235, 235)

# Text for icon+text rows always starts here, regardless of that row's
# icon size, so "Demons killed" and "Gold collected" line up with each
# other rather than each hugging its own (differently sized) icon.
STAT_ICON_X = settings.VIRTUAL_WIDTH // 2 - 90
STAT_ICON_COLUMN_WIDTH = 32
STAT_TEXT_X = STAT_ICON_X + STAT_ICON_COLUMN_WIDTH + 8

DEMON_ICON_SIZE = 56
# Matches SmallDemon's own "run" animation interval (src.entities.
# SmallDemon) - not imported from there since that value is baked into
# an per-instance animation dict, not exposed as a reusable constant.
DEMON_RUN_FRAME_INTERVAL = 0.1
DEMON_RUN_FRAMES = list(range(8, 16))

GOLD_ICON_SIZE = 16

# Native item art is 16x16 (src.items.definitions.ITEMS) - composited
# with its 1px outline (same src.render.outline/ITEM_OUTLINE_COLORS
# treatment as src.items.Pickup.render, see _build_item_icon) onto an
# 18x18 canvas, then scaled up together so the outline scales with the
# icon instead of staying a flat 1px regardless of size.
ITEM_ICON_NATIVE_SIZE = 16
ITEM_OUTLINE_OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1))
ITEM_ICON_SCALE = 1.25
ITEM_ICON_GAP = 6


def _build_item_icon(texture_id: str, frame_index: int) -> pygame.Surface:
    """Native 16x16 item art plus its 1px outline (see ITEM_ICON_SCALE's
    comment above), scaled up as one composite so the outline stays
    proportional to the icon instead of a flat 1px sliver next to a much
    bigger icon.
    """
    canvas_size = ITEM_ICON_NATIVE_SIZE + 2
    canvas = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)

    image = render.sprite(texture_id, frame_index)
    outline_color = settings.ITEM_OUTLINE_COLORS[texture_id]
    outline = render.outline(texture_id, frame_index, outline_color)
    for dx, dy in ITEM_OUTLINE_OFFSETS:
        canvas.blit(outline, (1 + dx, 1 + dy))
    canvas.blit(image, (1, 1))

    display_size = round(canvas_size * ITEM_ICON_SCALE)
    return pygame.transform.scale(canvas, (display_size, display_size))


class VictoryState(BaseState):
    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        play_music("victory")

        self.player: TypeVar("Player") = kwargs.get("player")
        self.elapsed_time: float = kwargs.get("elapsed_time", 0.0)

        self.blink_timer = 0.0
        self.show_prompt = True

        self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
        self.stat_font = pygame.font.Font(None, STAT_FONT_SIZE)
        self.small_font = pygame.font.Font(None, SMALL_FONT_SIZE)
        self.prompt_font = pygame.font.Font(None, PROMPT_FONT_SIZE)

        self.demon_icons = [
            pygame.transform.scale(
                render.sprite("small_demon", frame), (DEMON_ICON_SIZE, DEMON_ICON_SIZE)
            )
            for frame in DEMON_RUN_FRAMES
        ]
        self.gold_icon = pygame.transform.scale(
            render.sprite("gold_icon", 0), (GOLD_ICON_SIZE, GOLD_ICON_SIZE)
        )

        # Only the items actually picked up this run, in ITEMS' own
        # (registry) order, each paired with its final stack count.
        self.collected_items: List[Tuple[pygame.Surface, int]] = []
        if self.player is not None:
            for item_id, item in ITEMS.items():
                count = self.player.item_stacks[item_id]
                if count <= 0:
                    continue
                icon = _build_item_icon(item["texture_id"], item["frame_index"])
                self.collected_items.append((icon, count))

    def exit(self) -> None:
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        # "quit" (Esc) isn't handled here - Game.on_input already intercepts
        # it globally before it ever reaches the state machine.
        if input_id == "start" and input_data.pressed:
            self.state_machine.change("play")

    def update(self, dt: float) -> None:
        self.blink_timer += dt
        if self.blink_timer >= settings.TITLE_PROMPT_BLINK_INTERVAL:
            self.blink_timer -= settings.TITLE_PROMPT_BLINK_INTERVAL
            self.show_prompt = not self.show_prompt

    def _render_icon_stat(
        self, surface: pygame.Surface, icon: pygame.Surface, y: int, text: str
    ) -> None:
        icon_rect = icon.get_rect(midleft=(STAT_ICON_X, y))
        surface.blit(icon, icon_rect)
        render_text(
            surface,
            text,
            self.stat_font,
            STAT_TEXT_X,
            y - self.stat_font.get_height() // 2,
            STAT_COLOR,
            shadowed=True,
        )

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)

        render_text(
            surface,
            "Victory!",
            self.title_font,
            settings.VIRTUAL_WIDTH // 2,
            TITLE_Y,
            TITLE_COLOR,
            center=True,
            shadowed=True,
        )

        if self.player is None:
            return

        minutes, seconds = divmod(int(self.elapsed_time), 60)
        render_text(
            surface,
            f"Time survived: {minutes:02d}:{seconds:02d}",
            self.stat_font,
            settings.VIRTUAL_WIDTH // 2,
            TIME_Y,
            STAT_COLOR,
            center=True,
            shadowed=True,
        )

        frame_index = int(
            pygame.time.get_ticks() / 1000 / DEMON_RUN_FRAME_INTERVAL
        ) % len(self.demon_icons)
        self._render_icon_stat(
            surface,
            self.demon_icons[frame_index],
            KILLS_Y,
            f"Demons killed: {self.player.kills_count}",
        )

        self._render_icon_stat(
            surface, self.gold_icon, GOLD_Y, f"Gold collected: {self.player.gold}"
        )

        render_text(
            surface,
            f"Damage dealt: {int(self.player.total_damage_dealt)}",
            self.stat_font,
            settings.VIRTUAL_WIDTH // 2,
            DAMAGE_Y,
            STAT_COLOR,
            center=True,
            shadowed=True,
        )

        if self.collected_items:
            render_text(
                surface,
                "Items collected",
                self.stat_font,
                settings.VIRTUAL_WIDTH // 2,
                ITEMS_LABEL_Y,
                STAT_COLOR,
                center=True,
                shadowed=True,
            )

            row_width = (
                sum(icon.get_width() + ITEM_ICON_GAP for icon, _ in self.collected_items)
                - ITEM_ICON_GAP
            )
            x = settings.VIRTUAL_WIDTH // 2 - row_width // 2
            for icon, count in self.collected_items:
                surface.blit(icon, (x, ITEMS_ROW_Y))
                render_text(
                    surface,
                    f"x{count}",
                    self.small_font,
                    x + icon.get_width() // 2,
                    ITEMS_ROW_Y + icon.get_height() + 2,
                    STAT_COLOR,
                    center=True,
                    shadowed=True,
                )
                x += icon.get_width() + ITEM_ICON_GAP

        if self.show_prompt:
            render_text(
                surface,
                "Press start to play again, Esc to quit",
                self.prompt_font,
                settings.VIRTUAL_WIDTH // 2,
                PROMPT_Y,
                PROMPT_COLOR,
                center=True,
                shadowed=True,
            )
