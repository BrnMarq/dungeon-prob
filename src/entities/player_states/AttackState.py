import settings
from src.entities.states.BaseEntityState import BaseEntityState


class AttackState(BaseEntityState):
    """Front-facing melee (Q ability) - plays Marze.png's 3-frame attack
    swing (timed to fit settings.PLAYER_ATTACK_DURATION, see Player's
    "attack" animation_defs) - see entity.attack_hitbox_rect() for the
    hitbox this lands with.

    HIT_DELAY is a plain time offset rather than frame-synced like
    enemy_states.AttackState's HIT_FRAME_INDEX, since the swing here is
    only 3 frames rather than a full wind-up/strike/recovery sequence.
    """

    HIT_DELAY = 0.1

    def enter(self) -> None:
        self.entity.change_animation("attack")
        self._elapsed = 0.0
        self._hit_landed = False
        self._update_vx()

    def _update_vx(self) -> None:
        """Rooted while grounded (a ground attack shouldn't slide), but
        mid-air keeps normal movement control so a jump-attack doesn't
        stall dead in the air - same speed/turning PlayingState uses.
        """
        if self.entity.on_ground:
            self.entity.vx = 0
            return

        if self.entity.move_direction != 0:
            self.entity.flipped = self.entity.move_direction < 0
        self.entity.vx = settings.PLAYER_SPEED * self.entity.move_direction

    def _land_hit(self) -> None:
        hitbox = self.entity.attack_hitbox_rect()
        for other in self.entity.level.entities:
            if other is self.entity or not hasattr(other, "take_damage"):
                continue
            if not hasattr(other, "get_collision_rect"):
                continue
            if not hitbox.colliderect(other.get_collision_rect()):
                continue

            other.take_damage(settings.PLAYER_ATTACK_DAMAGE)

    def update(self, dt: float) -> None:
        # Dropped, not buffered - a dash/jump/another attack pressed while
        # mid-swing shouldn't fire the instant this state hands back to
        # PlayingState; the player has to press it again once they're
        # actually free to act on it.
        self.entity.dash_requested = False
        self.entity.attack_requested = False
        self.entity.jump_requested = False

        self._update_vx()
        self._elapsed += dt

        if not self._hit_landed and self._elapsed >= self.HIT_DELAY:
            self._hit_landed = True
            self._land_hit()

        if self._elapsed >= settings.PLAYER_ATTACK_DURATION:
            self.entity.change_state("playing")
