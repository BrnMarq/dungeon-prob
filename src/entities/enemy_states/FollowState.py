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

        if self.entity.melee_range_rect().colliderect(target.get_collision_rect()):
            self.entity.change_state("attack")
            return

        dx = target.x - self.entity.x
        self.entity.move_direction = 1 if dx > 0 else -1
        self.entity.flipped = self.entity.move_direction < 0
        self.entity.vx = settings.DEMON_SPEED * self.entity.move_direction
