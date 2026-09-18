"""
Background music playback, one looping track at a time through pygame's
single music channel (pygame.mixer.music) - separate from settings.SOUNDS'
short one-shot pygame.mixer.Sound effects, which play on their own
channels and don't interrupt each other.

Track changes cross-fade: the outgoing track fades out over FADE_OUT_MS,
then the new one fades in over FADE_IN_MS. pygame.mixer.music is a single
stream, so the two can't actually overlap - the next track can only start
once the current one has genuinely stopped - but sequencing a fade-out
immediately into a fade-in reads the same to the ear as a real crossfade.
Sequencing is driven by gale.timer.Timer, which gale.game.Game already
steps once a frame on its own (see gale.game.Game._Game__update), so
nothing here needs its own update() hook.
"""

import pygame

from gale.timer import Timer

import settings

FADE_OUT_MS = 800
FADE_IN_MS = 800

_current_track_id = None
_pending_fade_in = None


def play_music(track_id: str, loops: int = -1) -> None:
    """Cross-fades from whatever's currently playing to
    settings.MUSIC[track_id]. A no-op if that track is already the one
    playing (or already mid-transition-in), so re-entering a state (e.g.
    PlayState._reset_level's level doesn't re-enter PlayState, but
    nothing stops a future caller from calling this redundantly) doesn't
    restart the track from the beginning.

    :param track_id: Key into settings.MUSIC.
    :param loops: Forwarded to pygame.mixer.music.play() - -1 loops
        forever, 0 plays once.
    """
    global _current_track_id, _pending_fade_in

    if track_id == _current_track_id:
        return

    _current_track_id = track_id

    if _pending_fade_in is not None:
        _pending_fade_in.remove()
        _pending_fade_in = None

    def _fade_in() -> None:
        global _pending_fade_in
        pygame.mixer.music.load(settings.MUSIC[track_id])
        pygame.mixer.music.play(loops, fade_ms=FADE_IN_MS)
        _pending_fade_in = None

    if pygame.mixer.music.get_busy():
        pygame.mixer.music.fadeout(FADE_OUT_MS)
        _pending_fade_in = Timer.after(FADE_OUT_MS / 1000, _fade_in)
    else:
        _fade_in()
