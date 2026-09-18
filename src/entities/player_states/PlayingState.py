import settings
from src.entities.climbing import is_touching_climbable
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

        if self.entity.vertical_direction != 0 and is_touching_climbable(self.entity):
            self.entity.change_state("climb")
            return

        if self.entity.attack_requested:
            self.entity.attack_requested = False
            self.entity.change_state("attack")
            return

        if self.entity.throw_requested:
            self.entity.throw_requested = False
            if self.entity.throw_cooldown_timer <= 0:
                self.entity.throw_cooldown_timer = (
                    settings.PLAYER_THROW_COOLDOWN * self.entity.cooldown_multiplier
                )
                self.entity.change_state("throw")
                return

        if self.entity.dash_requested:
            self.entity.dash_requested = False
            if self.entity.dash_cooldown_timer <= 0:
                direction = -1 if self.entity.flipped else 1
                self.entity.dash_cooldown_timer = (
                    settings.PLAYER_DASH_COOLDOWN * self.entity.cooldown_multiplier
                )
                self.entity.change_state("dash", direction)
                return

        if self.entity.rage_requested:
            self.entity.rage_requested = False
            if self.entity.rage_cooldown_timer <= 0:
                self.entity.rage_cooldown_timer = (
                    settings.PLAYER_RAGE_COOLDOWN * self.entity.cooldown_multiplier
                )
                self.entity.change_state("rage")
                return

        self.entity.change_animation(
            "run" if self.entity.move_direction != 0 else "idle"
        )

        self.entity.vx = self.entity.speed * self.entity.move_direction

        if self.entity.jump_requested:
            self.entity.jump_requested = False
            if self.entity.on_ground:
                self.entity.vy = -settings.JUMP_TAKEOFF_SPEED
