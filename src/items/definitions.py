"""
Effects registry for stat-boosting item pickups (src.items.Pickup). Each
entry only needs a sprite frame index - the *effect* of picking one up
is resolved by src.entities.Player.collect_item keying on the item id,
since each effect touches a different Player stat in a different way
(additive vs. compounding) and forcing that into a generic shape here
would be more machinery than eight items justifies. Generalize this once
a ninth item needs a genuinely uniform "modify stat X by Y" shape.
"""

from typing import Dict

ITEM_CANE = "cane"
ITEM_HEART = "heart"
ITEM_KNIFE = "knife"
ITEM_SHIELD = "shield"
ITEM_DAGGERS = "daggers"
ITEM_HUNTERS_HAT = "hunters_hat"
ITEM_CATS_SPIRIT = "cats_spirit"
ITEM_LOADSTONE = "loadstone"

# assets/graphics/items.png - 128x16, eight 16x16 icons, row-major.
ITEMS: Dict[str, Dict[str, int]] = {
    ITEM_CANE: {"frame_index": 0},
    ITEM_HEART: {"frame_index": 1},
    ITEM_KNIFE: {"frame_index": 2},
    ITEM_SHIELD: {"frame_index": 3},
    ITEM_DAGGERS: {"frame_index": 4},
    ITEM_HUNTERS_HAT: {"frame_index": 5},
    ITEM_CATS_SPIRIT: {"frame_index": 6},
    ITEM_LOADSTONE: {"frame_index": 7},
}
