from typing import Any, Optional, TypeVar

import pygame

import settings
from src.entities.DamageNumber import DamageNumber
from src.entities.Entity import Entity
from src.entities.enemy_states import AttackState, DeadState, FollowState, HurtState, IdleState


class SmallDemon(Entity):
    """Ground enemy using assets/graphics/small-demon.png. Chases target
    horizontally (FollowState) and attacks once it's close enough
    (AttackState), pausing after the attack before resuming the chase.
    Falls back to IdleState if it has no target. take_damage() interrupts
    whatever it's doing to play HurtState, or DeadState once hp runs out.
    """

    # Matches the creature's actual silhouette within its padded 100x100
    # cell (see settings.FRAMES['small_demon']), not the raw cell size -
    # keeps the hitbox sane relative to the 16px tile grid.
    WIDTH = 20
    HEIGHT = 22

    # Tells src.map.Level.render to draw the overhead health bar
    # (src/ui/health_bar.py) for this entity whenever it's below full hp.
    SHOW_HEALTH_BAR = True

    def __init__(
        self,
        x: float,
        y: float,
        level: TypeVar("Level"),
        target: Optional[Any] = None,
    ) -> None:
        super().__init__(
            x,
            y,
            self.WIDTH,
            self.HEIGHT,
            "small_demon",
            level,
            states={
                "idle": lambda sm: IdleState(self, sm),
                "follow": lambda sm: FollowState(self, sm),
                "attack": lambda sm: AttackState(self, sm),
                "hurt": lambda sm: HurtState(self, sm),
                "dead": lambda sm: DeadState(self, sm),
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
        self.max_hp = settings.DEMON_MAX_HP
        self.hp = self.max_hp
        self.target = target
        self.change_state("follow" if target is not None else "idle")

    def take_damage(self, amount: int) -> None:
        """Reacts to incoming damage - see src.entities.player_states.
        AttackState._land_hit. Guarded by hp<=0 so a demon already dying
        doesn't restart HurtState/spawn extra damage numbers if something
        hits it again mid-death-animation.
        """
        if self.hp <= 0:
            return

        self.hp = max(0, self.hp - amount)
        self.level.entities.append(
            DamageNumber(self.x + self.width / 2, self.y, amount)
        )
        self.change_state("dead" if self.hp <= 0 else "hurt")

    def melee_range_rect(self) -> pygame.Rect:
        """The world-space rect FollowState checks to trigger an attack and
        AttackState re-checks before actually landing the hit - single
        source of truth so "when to attack" and "does it land" never
        disagree with each other or with the debug overlay.

        Extends settings.DEMON_ATTACK_RANGE past the entity's own hurtbox
        only on the side it's currently facing (self.flipped - set by
        FollowState from move_direction) - a demon facing right doesn't
        also threaten whatever is behind it.
        """
        if self.flipped:
            x = self.x - settings.DEMON_ATTACK_RANGE
        else:
            x = self.x
        return pygame.Rect(
            x,
            self.y,
            settings.DEMON_ATTACK_RANGE + self.width,
            self.height,
        )

    def get_attack_hitbox_rect(self) -> Optional[pygame.Rect]:
        """Debug-overlay hook (src/debug.py, src/map/Level.py) - only
        exposed while actually mid-swing, not for the whole time FollowState
        is chase-range-checking.
        """
        if not isinstance(self.state_machine.current, AttackState):
            return None
        return self.melee_range_rect()
