"""
Shared "Press X to Y" world-space overlay text for interactable
entities (src.entities.Chest, src.entities.Altar) - each entity decides
for itself when it's interactable and calls render() with its own
prompt(s), the same way Chest already draws its own cost text above
itself rather than some outside system tracking "what's the player near
right now."
"""

from typing import Iterable, Tuple

import pygame

from gale.text import render_text

import settings

_FONT = pygame.font.Font(None, 12)
_TEXT_COLOR = pygame.Color(235, 235, 235)
_LINE_HEIGHT = _FONT.get_height() + 2


def render(
    surface: pygame.Surface,
    center_x: int,
    near_y: int,
    prompts: Iterable[Tuple[str, str]],
) -> None:
    """Draws one "Press <key> to <action>" line per prompt, stacked
    upward so the last entry sits closest to the entity.

    :param center_x: Screen-space x to center every line on.
    :param near_y: Screen-space y (vertical center) of the LAST prompt -
        the one closest to the entity. Earlier prompts stack above it.
    :param prompts: (input_id, action) pairs in top-to-bottom order,
        e.g. [("interact", "Finish Run"), ("reset", "Reset Level")].
        input_id is looked up in settings.INPUT_KEY_LABELS for its
        displayed key.
    """
    prompts = list(prompts)
    for i, (input_id, action) in enumerate(reversed(prompts)):
        render_text(
            surface,
            f"Press {settings.INPUT_KEY_LABELS[input_id]} to {action}",
            _FONT,
            center_x,
            near_y - i * _LINE_HEIGHT,
            _TEXT_COLOR,
            center=True,
            shadowed=True,
        )
