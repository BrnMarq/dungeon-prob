"""
Shared tile helper: whether an entity's hurtbox overlaps a "vines" tile
whose collision property is "climbable". Used by both
src.entities.player_states.ClimbState (arrow-key climbing) and
src.entities.enemy_states.ClimbState (AI climbing to follow its target)
- neither the "vines" layer name nor the "climbable" property value mean
anything to gale.tilemap itself (see collision_type_at, which only ever
recognizes "solid"/"platform"), so this checks for them directly.
"""

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
