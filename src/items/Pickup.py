"""
A stat-boosting item pickup (assets/graphics/items.png - see
src.items.definitions.ITEMS for frame indices). Duck-typed the same way
as src.entities.ThrownSword/DamageNumber (update/render/is_dead, plus
get_collision_rect) so src.map.Level's entities list needs no
special-casing. Touching the player applies its stat via
Player.collect_item and removes itself - no VFX/SFX, no respawn.
"""

from typing import Any, TypeVar

import pygame

import settings
from src.items.definitions import ITEMS


class Pickup:
    TEXTURE_ID = "items"
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
        self.frame_index = ITEMS[item_id]["frame_index"]

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def update(self, dt: float) -> None:
        if self.get_collision_rect().colliderect(self.player.get_collision_rect()):
            self.player.collect_item(self.item_id)
            self.is_dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        texture = settings.TEXTURES[self.TEXTURE_ID]
        frame = settings.FRAMES[self.TEXTURE_ID][self.frame_index]
        image = pygame.Surface((frame.width, frame.height), pygame.SRCALPHA)
        image.fill((0, 0, 0, 0))
        image.blit(texture, (0, 0), frame)

        dest = camera.apply(pygame.Rect(self.x, self.y, self.width, self.height))
        surface.blit(image, dest)
