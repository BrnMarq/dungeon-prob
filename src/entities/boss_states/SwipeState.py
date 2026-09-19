import settings
from src.entities.boss_states.SwingState import SwingState


class SwipeState(SwingState):
    """The guardian's close-range attack - boss-reaper.png's 9-frame
    scythe swipe (frames 36-44), drawing assets/graphics/boss/
    slash-effect-norm.png over the swing. The attack a teleport always
    chains into (see TeleportState).
    """

    ATTACK_ID = "swipe"
    ANIMATION_ID = "swipe"
    SLASH_TEXTURE_ID = "slash_norm"
    SLASH_FRAME_INTERVAL = settings.SLASH_NORM_FRAME_INTERVAL
    HIT_FRAME_INDEX = settings.BOSS_SWIPE_HIT_FRAME_INDEX
    DAMAGE_ATTRIBUTE = "swipe_damage"
