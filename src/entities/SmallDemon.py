from typing import TypeVar

from src.entities.Entity import Entity
from src.entities.enemy_states import IdleState


class SmallDemon(Entity):
    """Ground enemy using assets/graphics/small-demon.png. Idle-only for now
    - see IdleState. run/attack/hurt/dead animations are registered so a
    later pass can wire up real AI/combat without re-deriving frame ranges.
    """

    # Matches the creature's actual silhouette within its padded 100x100
    # cell (see settings.FRAMES['small_demon']), not the raw cell size -
    # keeps the hitbox sane relative to the 16px tile grid.
    WIDTH = 20
    HEIGHT = 22

    def __init__(self, x: float, y: float, level: TypeVar("Level")) -> None:
        super().__init__(
            x,
            y,
            self.WIDTH,
            self.HEIGHT,
            "small_demon",
            level,
            states={
                "idle": lambda sm: IdleState(self, sm),
            },
            animation_defs={
                "idle": {"frames": list(range(0, 6)), "interval": 0.15},
                "run": {"frames": list(range(8, 16)), "interval": 0.1},
                "attack": {"frames": list(range(24, 31)), "interval": 0.08, "loops": 1},
                "hurt": {"frames": list(range(32, 36)), "interval": 0.1, "loops": 1},
                "dead": {"frames": list(range(40, 44)), "interval": 0.15, "loops": 1},
            },
        )
        self.sprite_offset = (42, 37)
        self.change_state("idle")
