from typing import Any, Dict, Tuple

import pygame

from gale.input_handler import InputData
from gale.text import render_text

import settings
from src.audio import play_music
from src.map.Background import ParallaxBackground
from src.states.BaseState import BaseState

TITLE_FONT_SIZE = 48
PROMPT_FONT_SIZE = 16
TITLE_Y = settings.VIRTUAL_HEIGHT // 3
PROMPT_Y = TITLE_Y + TITLE_FONT_SIZE
TITLE_COLOR = pygame.Color(255, 230, 180)
PROMPT_COLOR = pygame.Color(235, 235, 235)


class _ScrollOffset:
    """Stand-in for a gale.camera.Camera, exposing only the `.offset`
    attribute ParallaxBackground.render actually reads - there's no
    real camera on the title screen, just a scroll position advancing
    on its own (see TitleState.update).
    """

    def __init__(self) -> None:
        self.offset: Tuple[float, float] = (0.0, 0.0)


class TitleState(BaseState):
    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        play_music("title")

        self.background = ParallaxBackground(
            settings.TITLE_BACKGROUND_LOOP_WIDTH, settings.VIRTUAL_WIDTH
        )
        self.scroll = _ScrollOffset()
        self.scroll_x = 0.0
        self.blink_timer = 0.0
        self.show_prompt = True

        self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
        self.prompt_font = pygame.font.Font(None, PROMPT_FONT_SIZE)

    def exit(self) -> None:
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "start" and input_data.pressed:
            self.state_machine.change("play")

    def update(self, dt: float) -> None:
        # Wrapped rather than left to grow unbounded - see
        # settings.TITLE_BACKGROUND_LOOP_WIDTH's comment for why this
        # loop point isn't visible as anything worse than the
        # background's scattered tree instances resetting.
        self.scroll_x = (
            self.scroll_x + settings.TITLE_SCROLL_SPEED * dt
        ) % settings.TITLE_BACKGROUND_LOOP_WIDTH
        self.scroll.offset = (self.scroll_x, 0.0)

        self.blink_timer += dt
        if self.blink_timer >= settings.TITLE_PROMPT_BLINK_INTERVAL:
            self.blink_timer -= settings.TITLE_PROMPT_BLINK_INTERVAL
            self.show_prompt = not self.show_prompt

    def render(self, surface: pygame.Surface) -> None:
        self.background.render(surface, self.scroll)

        render_text(
            surface,
            settings.TITLE,
            self.title_font,
            settings.VIRTUAL_WIDTH // 2,
            TITLE_Y,
            TITLE_COLOR,
            center=True,
            shadowed=True,
        )

        if self.show_prompt:
            render_text(
                surface,
                "Press start to play",
                self.prompt_font,
                settings.VIRTUAL_WIDTH // 2,
                PROMPT_Y,
                PROMPT_COLOR,
                center=True,
                shadowed=True,
            )
