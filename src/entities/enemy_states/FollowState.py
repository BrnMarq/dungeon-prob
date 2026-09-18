import settings
from src.entities.climbing import is_touching_climbable, vertical_climb_direction
from src.entities.states.BaseEntityState import BaseEntityState


class FollowState(BaseEntityState):
    """Chases self.entity.target horizontally until close enough to
    attack, jumping over anything blocking the way (the same fixed-
    height jump the player uses - see settings.JUMP_TAKEOFF_SPEED) and
    grabbing onto a "vines" tile (src.entities.enemy_states.ClimbState)
    once the target is meaningfully above/below it (src.entities.
    climbing.vertical_climb_direction - below settings.
    DEMON_CLIMB_ALIGN_THRESHOLD pixels apart, it just keeps chasing on
    x instead, so it doesn't grab a vine right underfoot and get stuck
    trying to align on an already-close-enough row), so it can still
    close the distance if the ground path alone can't.
    """

    def enter(self) -> None:
        self.entity.change_animation("run")

    def update(self, dt: float) -> None:
        target = self.entity.target

        if target is None:
            self.entity.vx = 0
            return

        if self.entity.can_melee_target():
            self.entity.change_state("attack")
            return

        dx = target.x - self.entity.x
        self.entity.move_direction = 1 if dx > 0 else -1
        self.entity.flipped = self.entity.move_direction < 0
        self.entity.vx = settings.DEMON_SPEED * self.entity.move_direction

        if is_touching_climbable(self.entity) and vertical_climb_direction(
            self.entity, target
        ) != 0:
            self.entity.change_state("climb")
            return

        # collided_x reflects the previous frame's move (Entity.update
        # resolves it after this state's own update runs) - one frame
        # late, but that just means it jumps the frame after walking
        # into whatever blocked it, not the instant it does.
        if self.entity.on_ground and self.entity.collided_x:
            self.entity.vy = -settings.JUMP_TAKEOFF_SPEED
