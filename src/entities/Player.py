from typing import Optional, Tuple, TypeVar

import pygame

from gale.command import CommandBindings
from gale.input_handler import InputData

import settings
from src.commands import (
    ATTACK,
    DASH,
    JUMP,
    MOVE_LEFT,
    MOVE_RIGHT,
    STOP_JUMP,
    STOP_MOVE_LEFT,
    STOP_MOVE_RIGHT,
)
from src.entities.DamageNumber import DamageNumber
from src.entities.Entity import Entity
from src.entities.player_states import AttackState, DashState, PlayingState


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
                "attack": lambda sm: AttackState(self, sm),
            },
            animation_defs={
                "idle": {"frames": [0, 1, 2, 3], "interval": 0.2},
                "run": {"frames": [5, 6, 7], "interval": 0.1},
                "dash": {
                    "frames": [10, 11, 12, 13, 14],
                    "interval": settings.PLAYER_DASH_DURATION / 5,
                    "loops": 1,
                },
                "attack": {
                    "frames": [15, 16, 17],
                    "interval": settings.PLAYER_ATTACK_DURATION / 3,
                    "loops": 1,
                },
            },
        )
        self.change_state("playing")

        # Marze.png's cells are padded larger than the 32x32 hitbox (to
        # give the attack swing room to animate) - re-centers the sprite
        # horizontally and keeps its feet at the hitbox's bottom edge,
        # measured from the idle frame's opaque-pixel bounding box.
        self.sprite_offset = (10, 3)

        self.level_num = 1
        self.max_hp = settings.PLAYER_MAX_HP
        self.hp = self.max_hp
        self.xp = 0
        self.xp_to_next_level = settings.PLAYER_XP_TO_NEXT_LEVEL

        self.dash_requested = False
        self.dash_cooldown_timer = 0.0
        self.attack_requested = False
        self.invincible_timer = 0.0

        self.command_bindings = CommandBindings()
        self.command_bindings.bind("move_left", press=MOVE_LEFT, release=STOP_MOVE_LEFT)
        self.command_bindings.bind(
            "move_right", press=MOVE_RIGHT, release=STOP_MOVE_RIGHT
        )
        self.command_bindings.bind("jump", press=JUMP, release=STOP_JUMP)
        self.command_bindings.bind("dash", press=DASH)
        self.command_bindings.bind("attack", press=ATTACK)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.command_bindings.dispatch(self, input_id, input_data)

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt
        if self.invincible_timer > 0:
            self.invincible_timer -= dt

    @property
    def is_invincible(self) -> bool:
        return self.invincible_timer > 0

    def take_damage(self, amount: int) -> None:
        """Reacts to incoming damage (see src.entities.enemy_states.
        AttackState._land_hit) - a no-op entirely while dashing's
        invincibility window is active (self.invincible_timer, started by
        src.entities.player_states.DashState).
        """
        if self.is_invincible:
            return

        self.hp = max(0, self.hp - amount)
        self.level.entities.append(
            DamageNumber(self.x + self.width / 2, self.y, amount)
        )

    def attack_hitbox_rect(self) -> pygame.Rect:
        """The world-space rect AttackState lands its hit against - facing
        the direction Marze is currently flipped toward, same convention
        as src.entities.SmallDemon.melee_range_rect.
        """
        if self.flipped:
            x = self.x - settings.PLAYER_ATTACK_RANGE
        else:
            x = self.x
        return pygame.Rect(
            x, self.y, settings.PLAYER_ATTACK_RANGE + self.width, self.height
        )

    def get_attack_hitbox_rect(self) -> Optional[pygame.Rect]:
        """Debug-overlay hook (src/debug.py, src/map/Level.py) - only
        exposed while actually mid-swing.
        """
        if not isinstance(self.state_machine.current, AttackState):
            return None
        return self.attack_hitbox_rect()

    def get_ability_cooldown(self, slot: int) -> Tuple[float, float]:
        """(seconds remaining, total cooldown) for src.ui.HUD's ability bar,
        indexed the same way as marze-abilities.png/Q-W-E-R: 0 attack, 1
        unused, 2 dash, 3 unused. (0, 0) means "not on cooldown" - covers
        both a ready ability and one with no cooldown at all (e.g. attack).
        """
        if slot == 2:
            return self.dash_cooldown_timer, settings.PLAYER_DASH_COOLDOWN
        return 0.0, 0.0
