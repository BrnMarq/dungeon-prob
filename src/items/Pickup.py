"""
A stat-boosting item pickup (assets/graphics/white-items.png and
red-items.png - see src.items.definitions.ITEMS for texture id/frame
index). Duck-typed the same way
as src.entities.ThrownSword/DamageNumber (update/render/is_dead, plus
get_collision_rect) so src.map.Level's entities list needs no
special-casing. Touching the player applies its stat via
Player.collect_item and removes itself - no VFX/SFX, no respawn.

Idles with the same sine-tween bob as ThrownSword's floating swords
(base_y + sin(elapsed * speed) * amplitude), and renders a silhouette
outline (settings.ITEM_OUTLINE_COLORS, keyed by texture id) a pixel
outside the sprite's own edges each frame - on top of (not instead of)
the white outline already baked into the art - so it reads as a glow
even against similarly-colored backgrounds.
"""

from typing import Any, TypeVar

import math

import pygame

import settings
from src import render
from src.entities.ItemPopup import ItemPopup
from src.items.definitions import ITEMS

_OUTLINE_OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1))


class Pickup:
    WIDTH = 16
    HEIGHT = 16

    def __init__(
        self,
        x: float,
        y: float,
        item_id: str,
        player: TypeVar("Player"),
        level: TypeVar("Level"),
    ) -> None:
        self.x = x
        self.y = y
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.item_id = item_id
        self.player = player
        self.level = level
        self.is_dead = False
        self.texture_id = ITEMS[item_id]["texture_id"]
        self.frame_index = ITEMS[item_id]["frame_index"]

        self.base_y = y
        self.float_elapsed = 0.0

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def update(self, dt: float) -> None:
        if self.get_collision_rect().colliderect(self.player.get_collision_rect()):
            self.player.collect_item(self.item_id)
            item = ITEMS[self.item_id]
            self.level.entities.append(
                ItemPopup(
                    self.x + self.width / 2,
                    self.y,
                    item["name"],
                    settings.ITEM_OUTLINE_COLORS[item["texture_id"]],
                )
            )
            self.is_dead = True
            return

        self.float_elapsed += dt
        self.y = self.base_y + math.sin(
            self.float_elapsed * settings.ITEM_FLOAT_SPEED
        ) * settings.ITEM_FLOAT_AMPLITUDE

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        image = render.sprite(self.texture_id, self.frame_index)

        dest = camera.apply(pygame.Rect(self.x, self.y, self.width, self.height))

        outline_color = settings.ITEM_OUTLINE_COLORS[self.texture_id]
        outline = render.outline(self.texture_id, self.frame_index, outline_color)
        for dx, dy in _OUTLINE_OFFSETS:
            render.blit(surface, outline, dest.move(dx, dy))

        render.blit(surface, image, dest)
