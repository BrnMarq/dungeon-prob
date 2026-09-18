import settings
from src.entities.climbing import is_touching_climbable
from src.entities.states.BaseEntityState import BaseEntityState


class ClimbState(BaseEntityState):
    """Entered from "follow" (see FollowState.update) once the entity is
    touching a climbable vines tile and its target sits meaningfully
    above/below it. Cancels gravity entirely - vy is driven straight off
    the target's vertical direction each frame, mirroring src.entities.
    player_states.ClimbState but aimed at the target instead of reading
    input. Exits back to "follow" once vertically close enough to the
    target to resume the horizontal chase, or once it drifts off the
    climbable tile entirely.
    """

    def enter(self) -> None:
        self.entity.change_animation("run")
        self.entity.vx = 0
        self.entity.vy = 0

    def update(self, dt: float) -> None:
        target = self.entity.target

        if target is None or not is_touching_climbable(self.entity):
            self.entity.change_state("follow")
            return

        if self.entity.can_melee_target():
            self.entity.change_state("attack")
            return

        dy = target.y - self.entity.y
        if abs(dy) <= settings.DEMON_CLIMB_ALIGN_THRESHOLD:
            self.entity.change_state("follow")
            return

        self.entity.vy = settings.CLIMB_SPEED * (1 if dy > 0 else -1)

        dx = target.x - self.entity.x
        self.entity.move_direction = 1 if dx > 0 else -1
        self.entity.flipped = self.entity.move_direction < 0
        self.entity.vx = settings.DEMON_SPEED * self.entity.move_direction
