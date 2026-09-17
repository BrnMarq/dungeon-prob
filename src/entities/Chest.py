"""
A gold-cost reward container spawned on solid ground from the map's
"chests" Tiled object layer (see src.states.PlayState.enter and
settings.CHEST_SPAWN_MIN/MAX). Duck-typed like src.items.Pickup
(update/render/is_dead, plus get_collision_rect) so src.map.Level's
entities list needs no special-casing - but static (no float bob) and
never removes itself, just settles on its opened frame permanently.

Pressing "interact" (see src.commands.InteractCommand) while touching a
closed chest the player can afford deducts its cost - settings.
CHEST_BASE_COST scaled by whatever difficulty tier was current the
moment this chest spawned (all chests spawn together at level start, so
they all share one cost for the whole run; nothing later in the run
changes it - only a future "next level" would spawn a fresh batch at
whatever tier is current then), rolls a random item - 90% common (ITEMS
entries with texture_id "items"), 10% rare ("red_items"), per settings.
CHEST_RED_ITEM_CHANCE - and plays chest.png's 5-frame opening animation.
The cost renders above the chest while it's still closed. The rolled
item isn't handed over immediately: it only spawns as a real Pickup
above the lid settings.CHEST_ITEM_REVEAL_DELAY seconds after the lid
finishes opening, so the player can run off and keep playing, then come
back and decide whether it's worth walking over to collect, rather than
it being forced on them the instant they open the chest.
"""

from typing import Any, TypeVar

import random

import pygame

from gale.text import render_text

import settings
from src.items.definitions import ITEMS
from src.items.Pickup import Pickup

_OPEN_FRAME_COUNT = 5  # chest.png frames 1-5, played after frame 0 (closed)
_COST_FONT = pygame.font.Font(None, 12)
_COST_TEXT_COLOR = pygame.Color(230, 200, 90)


class Chest:
    WIDTH = 16
    HEIGHT = 16

    def __init__(
        self,
        x: float,
        y: float,
        player: TypeVar("Player"),
        level: TypeVar("Level"),
    ) -> None:
        self.x = x
        self.y = y
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.player = player
        self.level = level
        self.is_dead = False

        # Locked in at spawn time, not read live - every chest on the map
        # spawns together at level start, so they all share one cost for
        # the whole run regardless of how the difficulty tier climbs later.
        self.cost = round(
            settings.CHEST_BASE_COST * level.difficulty_tier["reward_multiplier"]
        )

        self.opened = False
        self.opening = False
        self.frame_index = 0
        self._open_anim_timer = 0.0
        self._pending_item_id = None
        self._reveal_timer = 0.0
        self._item_spawned = False

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def _roll_item(self) -> str:
        texture_id = (
            "red_items" if random.random() < settings.CHEST_RED_ITEM_CHANCE else "items"
        )
        pool = [
            item_id
            for item_id, item in ITEMS.items()
            if item["texture_id"] == texture_id
        ]
        return random.choice(pool)

    def update(self, dt: float) -> None:
        if self.opening:
            self._open_anim_timer += dt
            self.frame_index = 1 + min(
                _OPEN_FRAME_COUNT - 1,
                int(self._open_anim_timer / settings.CHEST_OPEN_FRAME_INTERVAL),
            )
            if self.frame_index >= _OPEN_FRAME_COUNT:
                self.opening = False
                self.opened = True
            return

        if self.opened:
            if not self._item_spawned:
                self._reveal_timer += dt
                if self._reveal_timer >= settings.CHEST_ITEM_REVEAL_DELAY:
                    self._item_spawned = True
                    self.level.entities.append(
                        Pickup(
                            self.x,
                            self.y - Pickup.HEIGHT,
                            self._pending_item_id,
                            self.player,
                            self.level,
                        )
                    )
            return

        if not self.get_collision_rect().colliderect(self.player.get_collision_rect()):
            return

        if not self.player.interact_requested:
            return

        if self.player.gold < self.cost:
            return

        self.player.interact_requested = False
        self.player.gold -= self.cost
        self._pending_item_id = self._roll_item()
        self.opening = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        texture = settings.TEXTURES["chest"]
        frame = settings.FRAMES["chest"][self.frame_index]
        image = pygame.Surface((frame.width, frame.height), pygame.SRCALPHA)
        image.fill((0, 0, 0, 0))
        image.blit(texture, (0, 0), frame)

        dest = camera.apply(pygame.Rect(self.x, self.y, self.width, self.height))
        surface.blit(image, dest)

        if not self.opening and not self.opened:
            render_text(
                surface,
                str(self.cost),
                _COST_FONT,
                dest.centerx,
                dest.top - _COST_FONT.get_height() // 2,
                _COST_TEXT_COLOR,
                center=True,
                shadowed=True,
            )
