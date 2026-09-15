import math

import settings
from src.entities.states.BaseEntityState import BaseEntityState


class RageState(BaseEntityState):
    """Invincible radius burst (R ability) - plays Marze.png's row-5 3-frame
    wind-up ("rage"), holding on its last frame (loops=1, see
    gale.animation.Animation) for most of PLAYER_RAGE_DURATION, then swaps to
    "rage_reverse" (the same frames backward) so it winds back down right as
    the ability ends. Grants entity.invincible_timer for the full duration
    and lands PLAYER_RAGE_HITS hits, evenly spaced, against everything within
    PLAYER_RAGE_RADIUS of the player's center.
    """

    def enter(self) -> None:
        self.entity.change_animation("rage")
        self._elapsed = 0.0
        self._hits_landed = 0
        self._reverse_started = False
        self.entity.invincible_timer = settings.PLAYER_RAGE_DURATION

    def _update_vx(self) -> None:
        """Rooted while grounded (a ground burst shouldn't slide), but
        mid-air keeps normal movement control - same as AttackState.
        """
        if self.entity.on_ground:
            self.entity.vx = 0
            return

        if self.entity.move_direction != 0:
            self.entity.flipped = self.entity.move_direction < 0
        self.entity.vx = self.entity.speed * self.entity.move_direction

    def _land_hit(self) -> None:
        entity = self.entity
        center_x = entity.x + entity.width / 2
        center_y = entity.y + entity.height / 2
        for other in entity.level.entities:
            if other is entity or not hasattr(other, "take_damage"):
                continue
            if not hasattr(other, "get_collision_rect"):
                continue

            rect = other.get_collision_rect()
            other_center_x = rect.x + rect.width / 2
            other_center_y = rect.y + rect.height / 2
            distance = math.hypot(center_x - other_center_x, center_y - other_center_y)
            if distance > settings.PLAYER_RAGE_RADIUS:
                continue

            other.take_damage(entity.get_damage(settings.PLAYER_RAGE_DAMAGE))

    def update(self, dt: float) -> None:
        # Dropped, not buffered - see AttackState.update's identical guard.
        self.entity.dash_requested = False
        self.entity.attack_requested = False
        self.entity.throw_requested = False
        self.entity.rage_requested = False
        self.entity.jump_requested = False

        self._update_vx()
        self._elapsed += dt

        while (
            self._hits_landed < settings.PLAYER_RAGE_HITS
            and self._elapsed >= (self._hits_landed + 1) * settings.PLAYER_RAGE_HIT_INTERVAL
        ):
            self._hits_landed += 1
            self._land_hit()

        reverse_start = settings.PLAYER_RAGE_DURATION - (
            3 * settings.PLAYER_RAGE_ANIM_FRAME_INTERVAL
        )
        if not self._reverse_started and self._elapsed >= reverse_start:
            self._reverse_started = True
            self.entity.change_animation("rage_reverse")

        if self._elapsed >= settings.PLAYER_RAGE_DURATION:
            self.entity.change_state("playing")
