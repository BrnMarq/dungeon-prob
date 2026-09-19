"""
The pause menu (Resume/Save/Load/Quit), pushed onto src.Game.DungeonProb's
pause_stack (a gale.state.StateStack) when Esc is pressed, popped when
Esc is pressed again or "Resume" is chosen. Not a gale.state.StateMachine
state - StateStack.push/pop expects an already-constructed instance (with
its own enter()/exit(), called by push/pop themselves), so this is built
directly by Game rather than registered in any states dict, and takes the
stack and the owning Game instance directly in its constructor instead of
a state_machine.

Reachable from every top-level screen (title/play/game_over/victory),
per the design spec - Save is only meaningful while actually in
PlayState, Load works from anywhere (it fully replaces whatever
top-level state was showing with a freshly-loaded PlayState).
"""

from typing import Any, Dict, Tuple

import pygame

from gale.input_handler import InputData
from gale.save import SaveError
from gale.text import render_text

import settings
from src.states.PlayState import PlayState

TITLE_FONT_SIZE = 32
OPTION_FONT_SIZE = 18
MESSAGE_FONT_SIZE = 14

TITLE_Y = settings.VIRTUAL_HEIGHT // 3
OPTIONS_START_Y = TITLE_Y + 50
OPTION_SPACING = 28
MESSAGE_Y = OPTIONS_START_Y + 4 * OPTION_SPACING + 20

OVERLAY_COLOR = (0, 0, 0, 160)
TITLE_COLOR = pygame.Color(235, 235, 235)
OPTION_COLOR = pygame.Color(200, 200, 200)
SELECTED_COLOR = pygame.Color(255, 215, 90)
DISABLED_COLOR = pygame.Color(110, 110, 110)
MESSAGE_COLOR = pygame.Color(120, 220, 140)

OPTIONS = ["Resume", "Save", "Load", "Quit"]

MESSAGE_DURATION = 1.5


class PauseMenuState:
    def __init__(self, stack: Any, game: Any) -> None:
        self.stack = stack
        self.game = game

    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        self.selected = 0
        self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
        self.option_font = pygame.font.Font(None, OPTION_FONT_SIZE)
        self.message_font = pygame.font.Font(None, MESSAGE_FONT_SIZE)

        self.overlay = pygame.Surface(
            (settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), pygame.SRCALPHA
        )
        self.overlay.fill(OVERLAY_COLOR)

        self.message = ""
        self.message_timer = 0.0

    def exit(self) -> None:
        pass

    def _in_play(self) -> bool:
        return isinstance(self.game.state_machine.current, PlayState)

    def _option_enabled(self, option: str) -> bool:
        if option == "Save":
            return self._in_play()
        if option == "Load":
            return self.game.save_manager.exists(settings.SAVE_SLOT)
        return True

    def _show_message(self, text: str) -> None:
        self.message = text
        self.message_timer = MESSAGE_DURATION

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if not input_data.pressed:
            return

        if input_id == "move_up":
            self.selected = (self.selected - 1) % len(OPTIONS)
        elif input_id == "move_down":
            self.selected = (self.selected + 1) % len(OPTIONS)
        elif input_id == "start":
            self._activate(OPTIONS[self.selected])

    def _activate(self, option: str) -> None:
        if option == "Resume":
            self.stack.pop()
        elif option == "Save":
            if not self._in_play():
                self._show_message("Nothing to save")
                return
            data = self.game.state_machine.current.get_save_data()
            self.game.save_manager.save(settings.SAVE_SLOT, data)
            self._show_message("Saved!")
        elif option == "Load":
            if not self.game.save_manager.exists(settings.SAVE_SLOT):
                self._show_message("No save found")
                return
            try:
                data = self.game.save_manager.load(settings.SAVE_SLOT)
            except SaveError:
                self._show_message("Save file is corrupted")
                return
            self.game.state_machine.change("play", save_data=data)
            self.stack.pop()
        elif option == "Quit":
            self.game.quit()

    def update(self, dt: float) -> None:
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.overlay, (0, 0))

        render_text(
            surface,
            "Paused",
            self.title_font,
            settings.VIRTUAL_WIDTH // 2,
            TITLE_Y,
            TITLE_COLOR,
            center=True,
            shadowed=True,
        )

        for i, option in enumerate(OPTIONS):
            if not self._option_enabled(option):
                color = DISABLED_COLOR
            elif i == self.selected:
                color = SELECTED_COLOR
            else:
                color = OPTION_COLOR

            render_text(
                surface,
                option,
                self.option_font,
                settings.VIRTUAL_WIDTH // 2,
                OPTIONS_START_Y + i * OPTION_SPACING,
                color,
                center=True,
                shadowed=True,
            )

        if self.message:
            render_text(
                surface,
                self.message,
                self.message_font,
                settings.VIRTUAL_WIDTH // 2,
                MESSAGE_Y,
                MESSAGE_COLOR,
                center=True,
                shadowed=True,
            )
