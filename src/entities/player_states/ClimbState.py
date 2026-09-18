import settings
from src.entities.climbing import is_touching_climbable
from src.entities.states.BaseEntityState import BaseEntityState


class ClimbState(BaseEntityState):
    """Entered from "playing" (see PlayingState.update) once the player
    is touching a climbable vines tile and presses up/down. Cancels
    gravity entirely - vy is driven straight off vertical_direction each
    frame, so no input holds the player in place on the vine instead of
    falling. Horizontal movement still works, to shift between vine
    columns. Exits back to "playing" the moment the player either jumps
    (a deliberate let-go) or drifts off the climbable tile entirely
    (move_and_collide already moved them there by the time this checks).
    """

    def enter(self) -> None:
        self.entity.change_animation("idle")
        self.entity.vx = 0
        self.entity.vy = 0

    def update(self, dt: float) -> None:
        # Dropped, not buffered - same reasoning as DashState/AttackState's
        # identical guards: none of these actions make sense mid-climb.
        self.entity.attack_requested = False
        self.entity.throw_requested = False
        self.entity.dash_requested = False
        self.entity.rage_requested = False

        if self.entity.jump_requested:
            self.entity.jump_requested = False
            self.entity.vy = -settings.JUMP_TAKEOFF_SPEED
            self.entity.change_state("playing")
            return

        if not is_touching_climbable(self.entity):
            self.entity.change_state("playing")
            return

        if self.entity.move_direction != 0:
            self.entity.flipped = self.entity.move_direction < 0
        self.entity.vx = self.entity.speed * self.entity.move_direction
        self.entity.vy = settings.CLIMB_SPEED * self.entity.vertical_direction
