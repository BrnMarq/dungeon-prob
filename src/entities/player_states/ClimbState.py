import settings
from src.entities.states.BaseEntityState import BaseEntityState

# Same custom tile property collision_type_at reads ("solid"/"platform")
# but a value neither of those recognizes, so climbable tiles never
# block move_and_collide on the "ground" layer - only this module treats
# "climbable" as meaningful, and only on the "vines" layer.
_VINES_LAYER = "vines"
_CLIMBABLE = "climbable"


def is_touching_climbable(entity) -> bool:
    """
    :returns: Whether entity's hurtbox overlaps a "vines" tile whose
        collision property is "climbable" - checked the same way
        gale.tilemap.collision.collision_type_at checks "solid"/
        "platform", just against a different layer/property value.
    """
    tilemap = entity.tilemap
    min_row = max(0, int(entity.y // tilemap.tile_height))
    max_row = min(
        tilemap.rows - 1, int((entity.y + entity.height - 1) // tilemap.tile_height)
    )
    min_col = max(0, int(entity.x // tilemap.tile_width))
    max_col = min(
        tilemap.cols - 1, int((entity.x + entity.width - 1) // tilemap.tile_width)
    )

    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            gid = tilemap.get_gid(_VINES_LAYER, row, col)
            if gid == 0:
                continue
            if tilemap.properties_of_gid(gid).get("collision") == _CLIMBABLE:
                return True

    return False


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
