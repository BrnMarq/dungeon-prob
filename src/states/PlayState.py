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
from src.ui.HUD import HUD


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

        # 0 rather than DEMON_SPAWN_INTERVAL so the first demon spawns on
        # the very first update() tick instead of after a cold wait.
        self.spawn_timer = 0.0

        self.hud = HUD(self.player)

    def _spawn_demon(self) -> None:
        active_demons = sum(
            1 for entity in self.level.entities if isinstance(entity, SmallDemon)
        )
        if active_demons >= settings.DEMON_MAX_ACTIVE:
            return

        tile_width = self.level.tilemap.tile_width
        player_col = int(self.player.x // tile_width)
        distance = random.randint(
            settings.DEMON_SPAWN_MIN_DISTANCE_TILES,
            settings.DEMON_SPAWN_MAX_DISTANCE_TILES,
        )
        direction = random.choice((-1, 1))
        spawn_col = max(
            0, min(self.level.tilemap.cols - 1, player_col + direction * distance)
        )

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

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = settings.DEMON_SPAWN_INTERVAL
            self._spawn_demon()

    def render(self, surface: pygame.Surface) -> None:
        self.level.render(surface, self.camera)
        self.hud.render(surface)
