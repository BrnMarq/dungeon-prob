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
        self.entity.vx = 0
        self.entity.change_animation("attack")
        self._elapsed = 0.0
        self._hit_landed = False

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
        self.entity.vx = 0
        self._elapsed += dt

        if not self._hit_landed and self._elapsed >= self.HIT_DELAY:
            self._hit_landed = True
            self._land_hit()

        if self._elapsed >= settings.PLAYER_ATTACK_DURATION:
            self.entity.change_state("playing")
