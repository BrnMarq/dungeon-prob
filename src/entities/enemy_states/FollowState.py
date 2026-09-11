import settings
from src.entities.states.BaseEntityState import BaseEntityState


class FollowState(BaseEntityState):
    """Chases self.entity.target horizontally until close enough to attack."""

    def enter(self) -> None:
        self.entity.change_animation("run")

    def update(self, dt: float) -> None:
        target = self.entity.target

        if target is None:
            self.entity.vx = 0
            return

        dx = target.x - self.entity.x

        if abs(dx) <= settings.DEMON_ATTACK_RANGE:
            self.entity.change_state("attack")
            return

        self.entity.move_direction = 1 if dx > 0 else -1
        self.entity.flipped = self.entity.move_direction < 0
        self.entity.vx = settings.DEMON_SPEED * self.entity.move_direction
