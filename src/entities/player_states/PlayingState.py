import settings
from src.entities.states.BaseEntityState import BaseEntityState


class PlayingState(BaseEntityState):
    """Single catch-all state driving Marze while there's only one sprite
    to show - ground/air movement and variable-height jumping, with no
    animation switching. Split into idle/walk/jump/fall once there are
    frames to tell them apart.
    """

    def enter(self) -> None:
        self.entity.change_animation("idle")

    def update(self, dt: float) -> None:
        if self.entity.move_direction != 0:
            self.entity.flipped = self.entity.move_direction < 0

        self.entity.vx = settings.PLAYER_SPEED * self.entity.move_direction

        if self.entity.jump_requested:
            self.entity.jump_requested = False
            if self.entity.on_ground:
                self.entity.vy = -settings.JUMP_TAKEOFF_SPEED

        # See settings.JUMP_TAKEOFF_SPEED/JUMP_CUT_VELOCITY for the
        # variable-height jump this implements.
        if not self.entity.jump_held and self.entity.vy < -settings.JUMP_CUT_VELOCITY:
            self.entity.vy = -settings.JUMP_CUT_VELOCITY
