from collections import Counter
from typing import Optional, Tuple, TypeVar

import math
import random

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
    RAGE,
    STOP_MOVE_LEFT,
    STOP_MOVE_RIGHT,
    THROW,
)
from src.entities.DamageNumber import DamageNumber
from src.entities.Entity import Entity
from src.entities.HitEffect import HitEffect
from src.entities.player_states import (
    AttackState,
    DashState,
    PlayingState,
    RageState,
    ThrowState,
)
from src.items.definitions import (
    ITEM_BLOOD_THIRST,
    ITEM_CANE,
    ITEM_CATS_SPIRIT,
    ITEM_DAGGERS,
    ITEM_HEART,
    ITEM_HUNTERS_HAT,
    ITEM_JIMBO,
    ITEM_KNIFE,
    ITEM_LOADSTONE,
    ITEM_SAMURAI_SWORD,
    ITEM_SHIELD,
    ITEM_SOUL_BOX,
)


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
                "throw": lambda sm: ThrowState(self, sm),
                "rage": lambda sm: RageState(self, sm),
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
                "throw": {
                    "frames": [20, 21, 22],
                    "interval": settings.PLAYER_THROW_DURATION / 3,
                    "loops": 1,
                },
                "rage": {
                    "frames": [25, 26, 27],
                    "interval": settings.PLAYER_RAGE_ANIM_FRAME_INTERVAL,
                    "loops": 1,
                },
                "rage_reverse": {
                    "frames": [27, 26, 25],
                    "interval": settings.PLAYER_RAGE_ANIM_FRAME_INTERVAL,
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
        self.gold = 0

        self.dash_requested = False
        self.dash_cooldown_timer = 0.0
        self.attack_requested = False
        self.throw_requested = False
        self.throw_cooldown_timer = 0.0
        self.rage_requested = False
        self.rage_cooldown_timer = 0.0
        self.invincible_timer = 0.0
        self.item_stacks: Counter = Counter()
        self.bonus_damage_from_kills = 0.0
        self.bonus_damage_from_level = 0.0

        self.command_bindings = CommandBindings()
        self.command_bindings.bind("move_left", press=MOVE_LEFT, release=STOP_MOVE_LEFT)
        self.command_bindings.bind(
            "move_right", press=MOVE_RIGHT, release=STOP_MOVE_RIGHT
        )
        self.command_bindings.bind("jump", press=JUMP)
        self.command_bindings.bind("dash", press=DASH)
        self.command_bindings.bind("attack", press=ATTACK)
        self.command_bindings.bind("ability_2", press=THROW)
        self.command_bindings.bind("ability_4", press=RAGE)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.command_bindings.dispatch(self, input_id, input_data)

    def update(self, dt: float) -> None:
        super().update(dt)
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt
        if self.throw_cooldown_timer > 0:
            self.throw_cooldown_timer -= dt
        if self.rage_cooldown_timer > 0:
            self.rage_cooldown_timer -= dt
        if self.invincible_timer > 0:
            self.invincible_timer -= dt

    @property
    def is_invincible(self) -> bool:
        return self.invincible_timer > 0

    def collect_item(self, item_id: str) -> None:
        """Called by src.items.Pickup.update on touch - bumps the stack
        count and, for the heart only, applies its effect immediately
        (max_hp/hp are plain fields, not derived, so there's nothing to
        recompute on demand the way speed/get_damage/attack_duration
        below are). The other eleven items have no state beyond the stack
        count itself at pickup time (the soul box's running kill bonus
        only grows later, via register_kill).
        """
        self.item_stacks[item_id] += 1
        if item_id == ITEM_HEART:
            self.max_hp += settings.ITEM_HP_BONUS
            self.hp += settings.ITEM_HP_BONUS

    @property
    def speed(self) -> float:
        """Effective move speed - settings.PLAYER_SPEED plus the walking
        cane's stacks, read by every state's movement instead of the raw
        setting. Dash stays on settings.PLAYER_DASH_SPEED, unaffected -
        it's a fixed burst, not "movement speed."
        """
        return settings.PLAYER_SPEED * (
            1 + settings.ITEM_SPEED_BONUS * self.item_stacks[ITEM_CANE]
        )

    def get_damage(self, base: float) -> int:
        """base scaled by the bloody knife's stacks, plus the soul box's
        running kill bonus, then rolled against the hunter's hat's crit
        chance for a flat damage multiplier (also shaving cooldowns via
        the blood thirst on a crit), and finally jimbo's flat multiplier
        if owned at all. Called by AttackState/RageState with their own
        damage constant, by ThrowState when spawning a ThrownSword, and
        by maybe_trigger_samurai_burst for its own burst damage.
        """
        damage = base * (1 + settings.ITEM_DAMAGE_BONUS * self.item_stacks[ITEM_KNIFE])
        damage += self.bonus_damage_from_kills
        damage += self.bonus_damage_from_level
        if random.random() < self.crit_chance:
            damage *= settings.ITEM_CRIT_DAMAGE_MULTIPLIER
            self._reduce_cooldowns_on_crit()
        if self.item_stacks[ITEM_JIMBO] > 0:
            damage *= settings.ITEM_JIMBO_DAMAGE_MULTIPLIER
        return round(damage)

    @property
    def crit_chance(self) -> float:
        """Hunter's hat's stacks, linear and capped at 100% - read by
        get_damage.
        """
        return min(
            1.0, settings.ITEM_CRIT_CHANCE_BONUS * self.item_stacks[ITEM_HUNTERS_HAT]
        )

    def _reduce_cooldowns_on_crit(self) -> None:
        """Blood thirst's stacks - called by get_damage whenever its crit
        roll succeeds, shaving time off every cooldown currently counting
        down (never below 0). Fires on the roll itself, not on an actual
        on-target connect - get_damage is only ever called to resolve a
        real attack/throw/rage action, never speculatively.
        """
        reduction = (
            settings.ITEM_BLOOD_THIRST_COOLDOWN_REDUCTION
            * self.item_stacks[ITEM_BLOOD_THIRST]
        )
        if reduction <= 0:
            return
        self.dash_cooldown_timer = max(0.0, self.dash_cooldown_timer - reduction)
        self.throw_cooldown_timer = max(0.0, self.throw_cooldown_timer - reduction)
        self.rage_cooldown_timer = max(0.0, self.rage_cooldown_timer - reduction)

    def register_kill(self) -> None:
        """Called by an enemy's take_damage once its hp drops to 0 (see
        src.entities.SmallDemon.take_damage) - the soul box's stacks
        convert each kill into a permanent flat damage bonus, added by
        get_damage. A no-op at 0 stacks, so kills before picking it up
        (and kills entirely without it) contribute nothing.
        """
        self.bonus_damage_from_kills += (
            settings.ITEM_SOUL_BOX_BONUS_PER_KILL * self.item_stacks[ITEM_SOUL_BOX]
        )

    def grant_gold(self, amount: int) -> None:
        """Called on an enemy kill (see src.entities.SmallDemon.take_damage)
        with settings.DEMON_BASE_GOLD_REWARD scaled by the level's current
        difficulty multiplier - just a running total for src.ui.HUD to
        display, no spending yet.
        """
        self.gold += amount

    def grant_xp(self, amount: int) -> None:
        """Called on an enemy kill alongside grant_gold. Levels up as many
        times as the granted XP covers (each threshold multiplying by
        PLAYER_LEVEL_XP_MULTIPLIER, so leveling gets progressively harder),
        applying PLAYER_LEVEL_UP_HP_BONUS/DAMAGE_BONUS per level gained.
        Current hp is not topped up on level-up, only the max_hp ceiling.
        """
        self.xp += amount
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level_num += 1
            self.xp_to_next_level = round(
                self.xp_to_next_level * settings.PLAYER_LEVEL_XP_MULTIPLIER
            )
            self.max_hp += settings.PLAYER_LEVEL_UP_HP_BONUS
            self.bonus_damage_from_level += settings.PLAYER_LEVEL_UP_DAMAGE_BONUS

    def maybe_trigger_samurai_burst(self) -> None:
        """Samurai sword's stacks - called after any landed hit (melee,
        thrown sword, or rage, including the burst's own trigger sites -
        see AttackState._land_hit/RageState._land_hit/ThrownSword) to
        roll a rare chance of an extra rage-style AOE burst centered on
        the player, spawning a src.entities.HitEffect slash flash on each
        target it hits. Applies its damage directly to each target in
        range rather than going through another landed-hit call site, so
        a hit landed by the burst itself can never roll another burst.
        """
        chance = min(
            settings.ITEM_SAMURAI_PROC_CHANCE_CAP,
            settings.ITEM_SAMURAI_PROC_CHANCE * self.item_stacks[ITEM_SAMURAI_SWORD],
        )
        if chance <= 0 or random.random() >= chance:
            return

        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2
        for other in self.level.entities:
            if other is self or not hasattr(other, "take_damage"):
                continue
            if not hasattr(other, "get_collision_rect"):
                continue

            rect = other.get_collision_rect()
            distance = math.hypot(
                center_x - (rect.x + rect.width / 2),
                center_y - (rect.y + rect.height / 2),
            )
            if distance <= settings.PLAYER_RAGE_RADIUS:
                other.take_damage(self.get_damage(settings.PLAYER_RAGE_DAMAGE))
                HitEffect.spawn_on(self.level, other)

    @property
    def attack_duration(self) -> float:
        """settings.PLAYER_ATTACK_DURATION shortened by the short
        daggers' stacks (compounding, floored so it can never hit 0) -
        read by AttackState instead of the raw setting. The "attack"
        animation's own frame interval does NOT retime with this -
        see the design spec's Non-goals.
        """
        return max(
            settings.ITEM_ATTACK_DURATION_FLOOR,
            settings.PLAYER_ATTACK_DURATION
            * settings.ITEM_ATTACK_SPEED_FACTOR ** self.item_stacks[ITEM_DAGGERS],
        )

    @property
    def dodge_chance(self) -> float:
        """Cat's spirit's stacks, linear and capped below 100% - read by
        take_damage.
        """
        return min(
            settings.ITEM_DODGE_CHANCE_CAP,
            settings.ITEM_DODGE_CHANCE_BONUS * self.item_stacks[ITEM_CATS_SPIRIT],
        )

    @property
    def cooldown_multiplier(self) -> float:
        """Loadstone's stacks (compounding, floored so it can never hit
        0) - read by src.entities.player_states.PlayingState when
        setting the dash/throw/rage cooldown timers.
        """
        return max(
            settings.ITEM_COOLDOWN_REDUCTION_FLOOR,
            settings.ITEM_COOLDOWN_REDUCTION_FACTOR ** self.item_stacks[ITEM_LOADSTONE],
        )

    def take_damage(self, amount: int) -> None:
        """Reacts to incoming damage (see src.entities.enemy_states.
        AttackState._land_hit) - a no-op entirely while dashing's
        invincibility window is active (self.invincible_timer, started by
        src.entities.player_states.DashState), or when the cat's spirit's
        dodge chance rolls a dodge (no HP loss, "Dodged!" popup instead of
        a DamageNumber - same early-return shape as the invincibility
        check).
        """
        if self.is_invincible:
            return

        if random.random() < self.dodge_chance:
            self.level.entities.append(
                DamageNumber(
                    self.x + self.width / 2,
                    self.y,
                    "Dodged!",
                    settings.DODGE_TEXT_COLOR,
                )
            )
            return

        amount = round(
            amount * settings.ITEM_RESISTANCE_FACTOR ** self.item_stacks[ITEM_SHIELD]
        )
        self.hp = max(0, self.hp - amount)
        self.level.entities.append(
            DamageNumber(self.x + self.width / 2, self.y, amount)
        )

    def attack_hitbox_rect(self) -> pygame.Rect:
        """The world-space rect AttackState lands its hit against - mostly
        the strip in front of Marze's own hurtbox (facing the direction
        currently flipped toward), dipping PLAYER_ATTACK_INSET back inside
        it rather than sitting completely flush, but nowhere near covering
        the whole hurtbox the way it used to.
        """
        if self.flipped:
            x = self.x - settings.PLAYER_ATTACK_RANGE + settings.PLAYER_ATTACK_INSET
        else:
            x = self.x + self.width - settings.PLAYER_ATTACK_INSET
        return pygame.Rect(x, self.y, settings.PLAYER_ATTACK_RANGE, self.height)

    def get_attack_hitbox_rect(self) -> Optional[pygame.Rect]:
        """Debug-overlay hook (src/debug.py, src/map/Level.py) - only
        exposed while actually mid-swing.
        """
        if not isinstance(self.state_machine.current, AttackState):
            return None
        return self.attack_hitbox_rect()

    def get_rage_hitbox_circle(self) -> Optional[Tuple[float, float, float]]:
        """Debug-overlay hook (src/debug.py, src/map/Level.py) - (center_x,
        center_y, radius) of the R ability's hit area, only exposed while
        actually mid-burst. Mirrors get_attack_hitbox_rect's pattern, but a
        circle instead of a rect since RageState hits by distance, not
        rect overlap - see RageState._land_hit.
        """
        if not isinstance(self.state_machine.current, RageState):
            return None
        return (
            self.x + self.width / 2,
            self.y + self.height / 2,
            settings.PLAYER_RAGE_RADIUS,
        )

    def get_ability_cooldown(self, slot: int) -> Tuple[float, float]:
        """(seconds remaining, total cooldown) for src.ui.HUD's ability bar,
        indexed the same way as marze-abilities.png/Q-W-E-R: 0 attack, 1
        throw, 2 dash, 3 rage. (0, 0) means "not on cooldown" - covers
        both a ready ability and one with no cooldown at all (e.g. attack).
        """
        if slot == 1:
            return self.throw_cooldown_timer, settings.PLAYER_THROW_COOLDOWN
        if slot == 2:
            return self.dash_cooldown_timer, settings.PLAYER_DASH_COOLDOWN
        if slot == 3:
            return self.rage_cooldown_timer, settings.PLAYER_RAGE_COOLDOWN
        return 0.0, 0.0
