from typing import TypeVar

from gale.command import CommandBindings
from gale.input_handler import InputData

from src.commands import (
    JUMP,
    MOVE_LEFT,
    MOVE_RIGHT,
    STOP_JUMP,
    STOP_MOVE_LEFT,
    STOP_MOVE_RIGHT,
)
from src.entities.Entity import Entity
from src.entities.player_states import PlayingState


class Player(Entity):
    WIDTH = 32
    HEIGHT = 32

    def __init__(self, x: float, y: float, level: TypeVar("Level")) -> None:
        super().__init__(
            x,
            y,
            self.WIDTH,
            self.HEIGHT,
            "marze",
            level,
            states={
                "playing": lambda sm: PlayingState(self, sm),
            },
            animation_defs={
                "idle": {"frames": [0, 1, 2, 3], "interval": 0.2},
            },
        )
        self.change_state("playing")

        self.command_bindings = CommandBindings()
        self.command_bindings.bind(
            "move_left", press=MOVE_LEFT, release=STOP_MOVE_LEFT
        )
        self.command_bindings.bind(
            "move_right", press=MOVE_RIGHT, release=STOP_MOVE_RIGHT
        )
        self.command_bindings.bind("jump", press=JUMP, release=STOP_JUMP)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.command_bindings.dispatch(self, input_id, input_data)
