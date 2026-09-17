"""
Effects registry for stat-boosting item pickups (src.items.Pickup). Each
entry only needs a texture id + sprite frame index - the *effect* of
picking one up is resolved by src.entities.Player.collect_item keying on
the item id, since each effect touches a different Player stat in a
different way (additive vs. compounding) and forcing that into a generic
shape here would be more machinery than twelve items justifies.
Generalize this once a thirteenth item needs a genuinely uniform "modify
stat X by Y" shape.
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
ITEM_BLOOD_THIRST = "blood_thirst"
ITEM_SAMURAI_SWORD = "samurai_sword"
ITEM_JIMBO = "jimbo"
ITEM_SOUL_BOX = "soul_box"

# assets/graphics/white-items.png - 128x16, eight 16x16 icons, row-major.
# assets/graphics/red-items.png - 64x16, four 16x16 icons, row-major.
ITEMS: Dict[str, Dict[str, object]] = {
    ITEM_CANE: {"texture_id": "items", "frame_index": 0},
    ITEM_HEART: {"texture_id": "items", "frame_index": 1},
    ITEM_KNIFE: {"texture_id": "items", "frame_index": 2},
    ITEM_SHIELD: {"texture_id": "items", "frame_index": 3},
    ITEM_DAGGERS: {"texture_id": "items", "frame_index": 4},
    ITEM_HUNTERS_HAT: {"texture_id": "items", "frame_index": 5},
    ITEM_CATS_SPIRIT: {"texture_id": "items", "frame_index": 6},
    ITEM_LOADSTONE: {"texture_id": "items", "frame_index": 7},
    ITEM_BLOOD_THIRST: {"texture_id": "red_items", "frame_index": 0},
    ITEM_SAMURAI_SWORD: {"texture_id": "red_items", "frame_index": 1},
    ITEM_JIMBO: {"texture_id": "red_items", "frame_index": 2},
    ITEM_SOUL_BOX: {"texture_id": "red_items", "frame_index": 3},
}
