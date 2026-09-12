import settings
from src.entities.states.BaseEntityState import BaseEntityState


class DashState(BaseEntityState):
    """Short, gravity-cancelling horizontal burst. Locks vx to the dash
    speed and zeroes vy every frame for the duration so the burst reads as
    a straight line regardless of whatever jump/fall was in progress, then
    hands control back to "playing".
    """

    def enter(self, direction: int) -> None:
        self.entity.change_animation("dash")
        self.entity.vx = settings.PLAYER_DASH_SPEED * direction
        self.entity.vy = 0
        self.timer = settings.PLAYER_DASH_DURATION

    def update(self, dt: float) -> None:
        self.timer -= dt
        self.entity.vy = 0

        if self.timer <= 0:
            self.entity.change_state("playing")
