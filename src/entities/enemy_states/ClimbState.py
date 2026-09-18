import settings
from src.entities.climbing import climbable_column_center_x
from src.entities.states.BaseEntityState import BaseEntityState


class ClimbState(BaseEntityState):
    """Entered from "follow" (see FollowState.update) once the entity is
    touching a climbable vines tile and its target sits meaningfully
    above/below it. Cancels gravity entirely - vy is driven straight off
    the target's vertical direction each frame, mirroring src.entities.
    player_states.ClimbState but aimed at the target instead of reading
    input. The entity's x is snapped to the vine column's center every
    frame instead of being movable, so it climbs straight up/down. Exits
    back to "follow" once vertically close enough to the target to
    resume the horizontal chase, or once it drifts off the climbable
    tile entirely.
    """

    def enter(self) -> None:
        self.entity.change_animation("run")
        self.entity.vx = 0
        self.entity.vy = 0

    def update(self, dt: float) -> None:
        target = self.entity.target

        center_x = climbable_column_center_x(self.entity)
        if target is None or center_x is None:
            self.entity.change_state("follow")
            return

        if self.entity.can_melee_target():
            self.entity.change_state("attack")
            return

        dy = target.y - self.entity.y
        if abs(dy) <= settings.DEMON_CLIMB_ALIGN_THRESHOLD:
            self.entity.change_state("follow")
            return

        self.entity.x = center_x - self.entity.width / 2
        self.entity.vx = 0
        self.entity.vy = settings.CLIMB_SPEED * (1 if dy > 0 else -1)

        dx = target.x - self.entity.x
        self.entity.move_direction = 1 if dx > 0 else -1
        self.entity.flipped = self.entity.move_direction < 0
