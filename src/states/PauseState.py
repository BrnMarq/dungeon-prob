from typing import Any, Dict, Tuple

import pygame

from gale.input_handler import InputData

from src.states.BaseState import BaseState


class PauseState(BaseState):
    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        # TODO: remove once PauseState has its own screen - forwards
        # straight to PlayState so it can be exercised on its own.
        self.state_machine.change('play')

    def exit(self) -> None:
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pass
