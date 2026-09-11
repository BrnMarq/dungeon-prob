from typing import Any, Dict, Tuple

import pygame

from gale.camera import Camera
from gale.input_handler import InputData

import settings
from src.entities.Player import Player
from src.map.Level import Level
from src.states.BaseState import BaseState


class PlayState(BaseState):
    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        self.level = Level(settings.TILEMAPS['forest'])

        # Row 16 is the forest map's ground surface (tile_height 16px);
        # resting exactly on it, not a few pixels in, so move_and_collide's
        # one-way platform check (which needs the entity already at/above
        # the surface) picks it up on the very first frame.
        spawn_y = 16 * self.level.tilemap.tile_height - 16
        self.player = Player(16, spawn_y, self.level)
        self.level.entities.append(self.player)

        self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
        self.camera.bounds = self.level.get_rect()
        self.camera.follow(self.player, rate=settings.CAMERA_FOLLOW_RATE)
        self.camera.x, self.camera.y = self.player.x, self.player.y
        self.camera.update(0)

    def exit(self) -> None:
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.player.on_input(input_id, input_data)

    def update(self, dt: float) -> None:
        self.camera.update(dt)
        self.level.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.level.render(surface, self.camera)
