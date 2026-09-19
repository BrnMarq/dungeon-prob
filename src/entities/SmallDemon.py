from typing import Any, Dict, Optional, TypeVar

import pygame

import settings
from src.entities.DamageNumber import DamageNumber
from src.entities.Entity import Entity
from src.entities.enemy_states import (
    AttackState,
    ClimbState,
    DeadState,
    FollowState,
    HurtState,
    IdleState,
    SpawnState,
)


class SmallDemon(Entity):
    """Ground enemy using assets/graphics/small-demon.png. Emerges via
    SpawnState, then chases target horizontally (FollowState), jumping
    over anything blocking its way and climbing "vines" tiles
    (ClimbState) when the target is meaningfully above/below it, and
    attacks once it's close enough (AttackState), pausing after the
    attack before resuming the chase. Falls back to IdleState if it has
    no target. take_damage() interrupts whatever it's doing to play
    HurtState, or DeadState once hp runs out.
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
        hp_multiplier: float = 1.0,
        damage_multiplier: float = 1.0,
    ) -> None:
        super().__init__(
            x,
            y,
            self.WIDTH,
            self.HEIGHT,
            "small_demon",
            level,
            states={
                "spawn": lambda sm: SpawnState(self, sm),
                "idle": lambda sm: IdleState(self, sm),
                "follow": lambda sm: FollowState(self, sm),
                "climb": lambda sm: ClimbState(self, sm),
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
                "spawn": {"frames": list(range(48, 52)), "interval": 0.1, "loops": 1},
            },
        )
        self.sprite_offset = (42, 37)
        # Scaled by the current difficulty tier at spawn time (see
        # src.states.PlayState._spawn_demon) - an already-spawned demon
        # doesn't retroactively get stronger if the tier changes under it.
        self.max_hp = round(settings.DEMON_MAX_HP * hp_multiplier)
        self.hp = self.max_hp
        self.attack_damage = round(settings.DEMON_ATTACK_DAMAGE * damage_multiplier)
        self.target = target
        self.change_state("spawn")

    def to_save_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack_damage": self.attack_damage,
        }

    def apply_save_dict(self, data: Dict[str, Any]) -> None:
        """Overlays a to_save_dict() snapshot onto an already-constructed
        SmallDemon (see PlayState._load_from_save_data) - the caller is
        also responsible for calling self.change_state("follow")
        afterward, skipping the spawn animation a freshly-constructed
        demon would otherwise start in.
        """
        self.hp = data["hp"]
        self.max_hp = data["max_hp"]
        self.attack_damage = data["attack_damage"]

    def take_damage(self, amount: int) -> None:
        """Reacts to incoming damage - see src.entities.player_states.
        AttackState._land_hit. Guarded by hp<=0 so a demon already dying
        doesn't restart HurtState/spawn extra damage numbers - or register
        an extra kill - if something hits it again mid-death-animation.
        """
        if self.hp <= 0:
            return

        self.hp = max(0, self.hp - amount)
        self.level.entities.append(
            DamageNumber(self.x + self.width / 2, self.y, amount)
        )

        if self.hp <= 0:
            self.change_state("dead")
            if self.target is not None and hasattr(self.target, "register_kill"):
                self.target.register_kill()
            if self.target is not None and hasattr(self.target, "grant_gold"):
                multiplier = self.level.difficulty_tier["reward_multiplier"]
                self.target.grant_gold(
                    round(settings.DEMON_BASE_GOLD_REWARD * multiplier)
                )
                self.target.grant_xp(round(settings.DEMON_BASE_XP_REWARD * multiplier))
        else:
            self.change_state("hurt")

    def can_melee_target(self) -> bool:
        """Whether self.target is actually close enough to attack - used
        by FollowState/ClimbState to trigger "attack", and by AttackState.
        _land_hit to re-check at the moment the hit lands. Ground combat
        never needed a vertical check (both combatants are always on the
        same row there), but climbing can put the demon and its target on
        the same vine column while genuinely far apart vertically, where
        melee_range_rect's rect overlap alone can still (barely) clip -
        this adds the vertical proximity ground combat got for free.
        """
        target = self.target
        if target is None:
            return False
        if abs(target.y - self.y) > settings.DEMON_ATTACK_RANGE:
            return False
        return self.melee_range_rect().colliderect(target.get_collision_rect())

    def melee_range_rect(self) -> pygame.Rect:
        """The world-space rect FollowState checks to trigger an attack and
        AttackState re-checks before actually landing the hit - single
        source of truth so "when to attack" and "does it land" never
        disagree with each other.

        Just the strip past the entity's own hurtbox on the side it's
        currently facing (self.flipped - set by FollowState from
        move_direction), not overlapping the hurtbox itself - a demon
        facing right doesn't also threaten whatever is behind it.
        """
        if self.flipped:
            x = self.x - settings.DEMON_ATTACK_RANGE
        else:
            x = self.x + self.width
        return pygame.Rect(x, self.y, settings.DEMON_ATTACK_RANGE, self.height)
