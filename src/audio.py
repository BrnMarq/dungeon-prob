"""
Background music playback, one looping track at a time through pygame's
single music channel (pygame.mixer.music) - separate from settings.SOUNDS'
short one-shot pygame.mixer.Sound effects, which play on their own
channels and don't interrupt each other.
"""

import pygame

import settings

_current_track_id = None


def play_music(track_id: str, loops: int = -1) -> None:
    """Loads and plays settings.MUSIC[track_id], replacing whatever is
    currently playing. A no-op if that track is already the one playing,
    so re-entering a state (e.g. PlayState._reset_level's level doesn't
    re-enter PlayState, but nothing stops a future caller from calling
    this redundantly) doesn't restart the track from the beginning.

    :param track_id: Key into settings.MUSIC.
    :param loops: Forwarded to pygame.mixer.music.play() - -1 loops
        forever, 0 plays once.
    """
    global _current_track_id

    if track_id == _current_track_id:
        return

    pygame.mixer.music.load(settings.MUSIC[track_id])
    pygame.mixer.music.play(loops)
    _current_track_id = track_id
