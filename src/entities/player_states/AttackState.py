import settings
from src.entities.states.BaseEntityState import BaseEntityState


class AttackState(BaseEntityState):
    """Front-facing melee (Q ability). No dedicated sprite yet, so it just
    holds the idle animation for settings.PLAYER_ATTACK_DURATION - see
    entity.attack_hitbox_rect() for the hitbox this lands with.

    HIT_DELAY is a plain time offset (unlike enemy_states.AttackState's
    frame-synced hit, there's no attack animation to sync to yet).
    """

    HIT_DELAY = 0.1

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.change_animation("idle")
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
