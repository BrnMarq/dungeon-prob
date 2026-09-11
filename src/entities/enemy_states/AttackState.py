import settings
from src.entities.states.BaseEntityState import BaseEntityState


class AttackState(BaseEntityState):
    """Plays the attack animation once, then stands idle for
    settings.DEMON_ATTACK_COOLDOWN before FollowState resumes the chase.
    """

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.change_animation("attack")
        self._elapsed = 0.0
        self._switched_to_idle = False

        animation = self.entity.animations["attack"]
        self._attack_duration = animation.size * animation.interval

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self._elapsed += dt

        if not self._switched_to_idle and self._elapsed >= self._attack_duration:
            self.entity.change_animation("idle")
            self._switched_to_idle = True

        if self._elapsed >= self._attack_duration + settings.DEMON_ATTACK_COOLDOWN:
            self.entity.change_state("follow")
