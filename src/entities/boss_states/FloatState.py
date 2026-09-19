import math
import random

import settings
from src.entities.states.BaseEntityState import BaseEntityState

# Attack ids paired with the weight each is picked at, per situation -
# see _choose_attack. The guardian never repeats the same attack twice in
# a row (BossReaper.last_attack), so these only ever weight the others.
_CLOSE_WEIGHTS = {"swipe": 5, "long_slash": 3, "magic": 2, "teleport": 1}
_MID_WEIGHTS = {"long_slash": 4, "magic": 3, "teleport": 3, "swipe": 1}
_FAR_WEIGHTS = {"teleport": 5, "magic": 4}


class FloatState(BaseEntityState):
    """The guardian's idle/approach state, and the hub every attack
    returns to.

    It drifts toward a hover point beside the player, its feet
    settings.BOSS_HOVER_HEIGHT above the player's own (never landing -
    see BossReaper.update, which skips gravity and tile collision
    entirely), bobbing on a sine wave the same way src.entities.
    ThrownSword's floating swords do. After
    settings.BOSS_ATTACK_COOLDOWN seconds it picks its next attack,
    weighted by how far the player is horizontally: the scythe swipe up
    close, the long sweep at mid range, the magic cast and the teleport
    (which closes the gap itself) from further out.
    """

    def enter(self) -> None:
        self.entity.change_animation("idle")
        self._cooldown = settings.BOSS_ATTACK_COOLDOWN
        self._bob_phase = random.uniform(0, math.tau)

    def _choose_attack(self) -> str:
        distance = self.entity.horizontal_distance_to_target()
        if distance <= settings.BOSS_SWIPE_RANGE:
            weights = _CLOSE_WEIGHTS
        elif distance <= settings.BOSS_LONG_RANGE:
            weights = _MID_WEIGHTS
        else:
            weights = _FAR_WEIGHTS

        # Never the same attack twice running - a fight that opens with
        # three teleport-swipes in a row is unreadable no matter how
        # generous the individual telegraphs are.
        choices = {
            attack: weight
            for attack, weight in weights.items()
            if attack != self.entity.last_attack
        } or weights

        return random.choices(list(choices.keys()), weights=list(choices.values()))[0]

    def update(self, dt: float) -> None:
        target = self.entity.target
        if target is None:
            self.entity.vx = 0
            self.entity.vy = 0
            return

        self.entity.face_target()

        # Horizontal drift toward the player, vertical drift toward the
        # hover point above their head - both capped at BOSS_FLOAT_SPEED
        # so it closes in at a readable, chase-able pace. Inside half a
        # swipe's range it stops pushing horizontally rather than shoving
        # itself through the player.
        dx = (
            target.get_collision_rect().centerx
            - self.entity.get_collision_rect().centerx
        )
        if abs(dx) > settings.BOSS_SWIPE_RANGE / 2:
            self.entity.vx = settings.BOSS_FLOAT_SPEED * (1 if dx > 0 else -1)
        else:
            self.entity.vx = 0

        self._bob_phase += settings.BOSS_FLOAT_BOB_SPEED * dt
        hover_y = (
            target.get_collision_rect().bottom
            - settings.BOSS_HOVER_HEIGHT
            - self.entity.height
        )
        hover_y += math.sin(self._bob_phase) * settings.BOSS_FLOAT_AMPLITUDE
        dy = hover_y - self.entity.y
        self.entity.vy = max(
            -settings.BOSS_FLOAT_SPEED, min(settings.BOSS_FLOAT_SPEED, dy * 2)
        )

        self._cooldown -= dt
        if self._cooldown <= 0:
            self.entity.change_state(self._choose_attack())
