import random
from typing import Any, Dict, Tuple

import pygame

from gale.camera import Camera
from gale.input_handler import InputData

import settings
from src.entities.Player import Player
from src.entities.SmallDemon import SmallDemon
from src.map.Level import Level
from src.states.BaseState import BaseState


class PlayState(BaseState):
    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        self.level = Level(settings.TILEMAPS['forest'])

        # Row 16 is the forest map's ground surface (tile_height 16px);
        # resting exactly on it, not a few pixels in, so move_and_collide's
        # one-way platform check (which needs the entity already at/above
        # the surface) picks it up on the very first frame.
        spawn_y = 16 * self.level.tilemap.tile_height - Player.HEIGHT
        self.player = Player(16, spawn_y, self.level)
        self.level.entities.append(self.player)

        self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
        self.camera.bounds = self.level.get_rect()
        self.camera.follow(self.player, rate=settings.CAMERA_FOLLOW_RATE)
        self.camera.x, self.camera.y = self.player.x, self.player.y
        self.camera.update(0)

        self._spawn_demon_near_player()

    def _spawn_demon_near_player(self) -> None:
        tile_width = self.level.tilemap.tile_width
        half_view_cols = int((settings.VIRTUAL_WIDTH / 2) // tile_width)
        player_col = int(self.player.x // tile_width)
        min_col = max(0, player_col - half_view_cols)
        max_col = min(self.level.tilemap.cols - 1, player_col + half_view_cols)
        # Stay clear of the player's own column so it doesn't spawn on top
        # of them, but still within the camera's current view.
        candidate_cols = [
            col for col in range(min_col, max_col + 1) if abs(col - player_col) >= 3
        ]

        spawn_col = random.choice(candidate_cols) if candidate_cols else player_col
        row = self.level.ground_row(spawn_col)
        if row is None:
            return

        spawn_x = spawn_col * tile_width
        spawn_y = row * self.level.tilemap.tile_height - SmallDemon.HEIGHT
        demon = SmallDemon(spawn_x, spawn_y, self.level, target=self.player)
        self.level.entities.append(demon)

    def exit(self) -> None:
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.player.on_input(input_id, input_data)

    def update(self, dt: float) -> None:
        self.camera.update(dt)
        self.level.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.level.render(surface, self.camera)
