import settings
from src.entities.boss_states.SwingState import SwingState


class LongSlashState(SwingState):
    """The guardian's long sweep - boss-reaper.png's 12-frame row
    (frames 60-71), drawing assets/graphics/boss/slash-effect-wide.png
    over it.

    Deliberately the slowest of its attacks (settings.
    BOSS_LONG_FRAME_INTERVAL, over a second of wind-up) and the hardest
    hitting, reaching most of a screen-width out - the long telegraph is
    what makes BOSS_LONG_HIT_WIDTH fair rather than unavoidable.
    """

    ATTACK_ID = "long_slash"
    ANIMATION_ID = "long_slash"
    SLASH_TEXTURE_ID = "slash_wide"
    SLASH_FRAME_INTERVAL = settings.SLASH_WIDE_FRAME_INTERVAL
    HIT_FRAME_INDEX = settings.BOSS_LONG_HIT_FRAME_INDEX
    DAMAGE_ATTRIBUTE = "long_damage"
