from typing import Any, Dict, Tuple

import pygame

from gale.input_handler import InputData
from gale.text import render_text

import settings
from src.audio import play_music
from src.states.BaseState import BaseState

TITLE_FONT_SIZE = 48
PROMPT_FONT_SIZE = 16
TITLE_Y = settings.VIRTUAL_HEIGHT // 3
PROMPT_Y = TITLE_Y + TITLE_FONT_SIZE
BACKGROUND_COLOR = pygame.Color(20, 10, 10)
TITLE_COLOR = pygame.Color(200, 40, 40)
PROMPT_COLOR = pygame.Color(235, 235, 235)


class GameOverState(BaseState):
    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        play_music("game_over")

        self.blink_timer = 0.0
        self.show_prompt = True

        self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
        self.prompt_font = pygame.font.Font(None, PROMPT_FONT_SIZE)

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

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(BACKGROUND_COLOR)

        render_text(
            surface,
            "You Died",
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
                "Press start to try again, Esc to quit",
                self.prompt_font,
                settings.VIRTUAL_WIDTH // 2,
                PROMPT_Y,
                PROMPT_COLOR,
                center=True,
                shadowed=True,
            )
