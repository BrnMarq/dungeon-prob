from src.entities.climbing import climbable_column_center_x, vertical_climb_direction
from src.entities.states.BaseEntityState import BaseEntityState
import settings


class ClimbState(BaseEntityState):
    """Entered from "follow" (see FollowState.update) once the entity is
    touching a climbable vines tile and its target sits meaningfully
    above/below it. Cancels gravity entirely - vy is driven straight off
    src.entities.climbing.vertical_climb_direction each frame, mirroring
    src.entities.player_states.ClimbState but aimed at the target
    instead of reading input. The entity's x is snapped to the vine
    column's center every frame instead of being movable, so it climbs
    straight up/down. Exits back to "follow" (to resume the horizontal
    chase) the moment vertical_climb_direction says it's already close
    enough to the target's row not to bother climbing further, or once
    it drifts off the climbable tile entirely - checking the exact same
    threshold FollowState used to grab on in the first place, so the two
    states can never disagree and leave it oscillating between them.
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

        direction = vertical_climb_direction(self.entity, target)
        if direction == 0:
            self.entity.change_state("follow")
            return

        self.entity.x = center_x - self.entity.width / 2
        self.entity.vx = 0
        self.entity.vy = settings.CLIMB_SPEED * direction

        dx = target.x - self.entity.x
        self.entity.move_direction = 1 if dx > 0 else -1
        self.entity.flipped = self.entity.move_direction < 0
