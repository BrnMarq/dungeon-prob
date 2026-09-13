import settings
from src.entities.states.BaseEntityState import BaseEntityState


class PlayingState(BaseEntityState):
    """Single catch-all state driving Marze - ground/air movement and a
    fixed-height jump, switching between idle/run. Split further into
    jump/fall once there are frames to tell them apart.
    """

    def enter(self) -> None:
        self.entity.change_animation("idle")

    def update(self, dt: float) -> None:
        if self.entity.move_direction != 0:
            self.entity.flipped = self.entity.move_direction < 0

        if self.entity.attack_requested:
            self.entity.attack_requested = False
            self.entity.change_state("attack")
            return

        if self.entity.dash_requested:
            self.entity.dash_requested = False
            if self.entity.dash_cooldown_timer <= 0:
                direction = -1 if self.entity.flipped else 1
                self.entity.dash_cooldown_timer = settings.PLAYER_DASH_COOLDOWN
                self.entity.change_state("dash", direction)
                return

        self.entity.change_animation(
            "run" if self.entity.move_direction != 0 else "idle"
        )

        self.entity.vx = settings.PLAYER_SPEED * self.entity.move_direction

        if self.entity.jump_requested:
            self.entity.jump_requested = False
            if self.entity.on_ground:
                self.entity.vy = -settings.JUMP_TAKEOFF_SPEED
