from typing import TypeVar

from gale.command import CommandBindings
from gale.input_handler import InputData

import settings
from src.commands import (
    DASH,
    JUMP,
    MOVE_LEFT,
    MOVE_RIGHT,
    STOP_JUMP,
    STOP_MOVE_LEFT,
    STOP_MOVE_RIGHT,
)
from src.entities.Entity import Entity
from src.entities.player_states import DashState, PlayingState


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
                "dash": lambda sm: DashState(self, sm),
            },
            animation_defs={
                "idle": {"frames": [0, 1, 2, 3], "interval": 0.2},
                "run": {"frames": [5, 6, 7], "interval": 0.1},
                "dash": {
                    "frames": [10, 11, 12, 13, 14],
                    "interval": settings.PLAYER_DASH_DURATION / 5,
                    "loops": 1,
                },
            },
        )
        self.change_state("playing")

        self.level_num = 1
        self.max_hp = settings.PLAYER_MAX_HP
        self.hp = self.max_hp
        self.xp = 0
        self.xp_to_next_level = settings.PLAYER_XP_TO_NEXT_LEVEL

        self.dash_requested = False
        self.dash_cooldown_timer = 0.0

        self.command_bindings = CommandBindings()
        self.command_bindings.bind("move_left", press=MOVE_LEFT, release=STOP_MOVE_LEFT)
        self.command_bindings.bind(
            "move_right", press=MOVE_RIGHT, release=STOP_MOVE_RIGHT
        )
        self.command_bindings.bind("jump", press=JUMP, release=STOP_JUMP)
        self.command_bindings.bind("dash", press=DASH)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.command_bindings.dispatch(self, input_id, input_data)

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt
