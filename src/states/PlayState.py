import random
from typing import Any, Dict, Tuple

import pygame

from gale.camera import Camera
from gale.input_handler import InputData

import settings
from src.entities.Altar import Altar
from src.entities.Chest import Chest
from src.entities.Decoration import Decoration
from src.entities.Player import Player
from src.entities.SmallDemon import SmallDemon
from src.map.Level import Level
from src.states.BaseState import BaseState
from src.ui.HUD import HUD


class PlayState(BaseState):
    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        self.level = Level(settings.TILEMAPS['forest'])

        self._spawn_player()
        self.player = Player(
            self._spawn_center_x - Player.WIDTH / 2,
            self._spawn_ground_y - Player.HEIGHT,
            self.level,
        )
        self.level.entities.append(self.player)
        self._spawn_pillars()

        self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
        self.camera.bounds = self.level.get_rect()
        self.camera.follow(self.player, rate=settings.CAMERA_FOLLOW_RATE)
        self.camera.x, self.camera.y = self.player.x, self.player.y
        self.camera.update(0)

        # 0 rather than a spawn_interval wait so the first demon spawns on
        # the very first update() tick instead of after a cold wait.
        self.spawn_timer = 0.0
        self.elapsed_time = 0.0
        self.current_tier = settings.DIFFICULTY_TIERS[0]

        self.hud = HUD(self.player)
        self._spawn_chests()
        self._spawn_altar()

    def _spawn_player(self) -> None:
        """Picks the player's spawn column/ground row once per level -
        from a random point in the map's "spawns" object layer (same
        set-of-possible-points pattern as chests/altars), falling back to
        the map's leftmost column if that layer is ever empty. Looked up
        rather than hardcoded, so edits to the map's ground height don't
        leave the player spawning inside/below it, and stored on self
        rather than only returned so _reset_level and _spawn_pillars can
        reuse the exact same point instead of re-rolling it.

        Snaps to the platform at or below the point's own row (Level.
        ground_row's start_row) rather than scanning from the top of the
        map - this map has more than one platform stacked in the same
        column in places, and scanning from the top would land the
        player on whichever one happens to be topmost there, not the one
        the point was actually placed on.
        """
        tile_width = self.level.tilemap.tile_width
        tile_height = self.level.tilemap.tile_height
        spawn_points = self.level.tilemap.object_layers.get("spawns", [])
        if spawn_points:
            point = random.choice(spawn_points)
            center_x = point.x + point.width / 2
            start_row = int(point.y // tile_height)
        else:
            center_x = 16
            start_row = 0

        col = int(center_x // tile_width)
        row = self.level.ground_row(col, start_row=start_row)

        self._spawn_center_x = center_x
        # Resting exactly on the surface, not a few pixels in, so
        # move_and_collide's one-way platform check (which needs the
        # entity already at/above the surface) picks it up on the very
        # first frame.
        self._spawn_ground_y = row * self.level.tilemap.tile_height

    def _spawn_pillars(self) -> None:
        """Two static ruins-pillars.png decorations (src.entities.
        Decoration) flanking the spawn point _spawn_player just picked -
        purely cosmetic, no collision. The left pillar uses frame 0, the
        right uses frame 1, and the right one is horizontally flipped for
        a symmetric pair.
        """
        pillar_width, pillar_height = settings.FRAMES["ruins_pillars"][0].size
        gap = settings.PILLAR_SPAWN_GAP
        y = self._spawn_ground_y - pillar_height

        self.level.entities.append(
            Decoration(
                self._spawn_center_x - gap - pillar_width, y, "ruins_pillars", 0
            )
        )
        self.level.entities.append(
            Decoration(
                self._spawn_center_x + gap, y, "ruins_pillars", 1, flipped=True
            )
        )

    def _spawn_demon(self) -> None:
        """Rolls a random column at settings.DEMON_SPAWN_MIN/MAX_DISTANCE_
        TILES from the player, alternating sides, and re-rolls (up to
        DEMON_SPAWN_MAX_ATTEMPTS times) whenever that column has no
        ground_row - e.g. it landed over a gap/chasm - instead of giving
        up on the whole spawn tick, since spawn_timer has already been
        reset by the caller and a giveup here would silently skip that
        entire spawn_interval with nothing appearing.
        """
        tile_width = self.level.tilemap.tile_width
        player_col = int(self.player.x // tile_width)

        spawn_col = None
        row = None
        for _ in range(settings.DEMON_SPAWN_MAX_ATTEMPTS):
            distance = random.randint(
                settings.DEMON_SPAWN_MIN_DISTANCE_TILES,
                settings.DEMON_SPAWN_MAX_DISTANCE_TILES,
            )
            direction = random.choice((-1, 1))
            col = max(
                0, min(self.level.tilemap.cols - 1, player_col + direction * distance)
            )
            row = self.level.ground_row(col)
            if row is not None:
                spawn_col = col
                break

        if spawn_col is None:
            return

        spawn_x = spawn_col * tile_width
        spawn_y = row * self.level.tilemap.tile_height - SmallDemon.HEIGHT
        demon = SmallDemon(
            spawn_x,
            spawn_y,
            self.level,
            target=self.player,
            hp_multiplier=self.current_tier["enemy_hp_multiplier"],
            damage_multiplier=self.current_tier["enemy_damage_multiplier"],
        )
        self.level.entities.append(demon)

    def _spawn_chests(self) -> None:
        """One Chest per randomly-chosen point in the map's "chests"
        object layer (assets/maps/forest.json) - a set of possible spawn
        points, not every point gets a chest each run.
        """
        spawn_points = self.level.tilemap.object_layers.get("chests", [])
        count = min(
            len(spawn_points),
            random.randint(settings.CHEST_SPAWN_MIN, settings.CHEST_SPAWN_MAX),
        )
        for point in random.sample(spawn_points, count):
            self.level.entities.append(
                Chest(point.x, point.y, self.player, self.level)
            )

    def _spawn_altar(self) -> None:
        """One Altar (unlike chests, always exactly one) at a random point
        from the map's "altars" object layer. altars.png (80x80) is much
        bigger than the layer's own 16x16 points, and trusting the point's
        y directly (like the same-sized chests do) leaves it floating or
        sunk into the ground the moment the point isn't pixel-exact on a
        tile boundary. Instead, like the player/demon spawns, the actual
        ground row under the point's horizontal center is looked up via
        Level.ground_row, and Altar.spawn_position anchors the sprite's
        own art (not its padded cell's raw edges - see Altar.ART_BOTTOM/
        ART_CENTER_X) to that row's surface, centered on the point.

        Scans from the point's own row (Level.ground_row's start_row),
        same reasoning as _spawn_player - this map has more than one
        platform stacked in the same column in places, and scanning from
        the top of the map would land the altar on whichever platform
        happens to be topmost there, not the one the point was actually
        placed on.
        """
        spawn_points = self.level.tilemap.object_layers.get("altars", [])
        if not spawn_points:
            return
        point = random.choice(spawn_points)

        tile_width = self.level.tilemap.tile_width
        tile_height = self.level.tilemap.tile_height
        center_x = point.x + point.width / 2
        col = int(center_x // tile_width)
        start_row = int(point.y // tile_height)
        row = self.level.ground_row(col, start_row=start_row)
        if row is None:
            return

        ground_surface_y = row * self.level.tilemap.tile_height
        x, y = Altar.spawn_position(center_x, ground_surface_y)
        self.level.entities.append(Altar(x, y, self.player, self.level))

    def _reset_level(self) -> None:
        """Chosen at the altar once its buff has ended (level.altar_choice
        == "reset") - regenerates the map's contents (fresh chests, at
        whatever the current difficulty tier's reward_multiplier now
        costs; a fresh dormant Altar; the player back at the start) but
        leaves run time, difficulty tier, and all player stats (gold, xp,
        level, items, hp) untouched, since this is a "descend deeper,
        same run" choice, not a new game.
        """
        self.player.x = self._spawn_center_x - Player.WIDTH / 2
        self.player.y = self._spawn_ground_y - Player.HEIGHT
        self.player.vx = 0
        self.player.vy = 0

        self.level.entities = [self.player]
        self.level.altar_phase = "inactive"
        self.level.altar_buff_timer = 0.0
        self.spawn_timer = 0.0
        self._spawn_chests()
        self._spawn_altar()
        self._spawn_pillars()

        self.camera.x, self.camera.y = self.player.x, self.player.y
        self.camera.update(0)

    def exit(self) -> None:
        pass

    def on_input(self, input_id: str, input_data: InputData) -> None:
        self.player.on_input(input_id, input_data)

    def update(self, dt: float) -> None:
        self.camera.update(dt)
        self.level.update(dt)
        # Consumed by at most one Chest/Altar.update() above this frame (or
        # by none, if nothing was in range) - a single press should never
        # carry over and auto-trigger something reached on some later frame.
        self.player.interact_requested = False
        self.player.reset_requested = False

        if self.level.altar_choice == "final_level":
            self.level.altar_choice = None
            self.state_machine.change("victory")
            return
        if self.level.altar_choice == "reset":
            self.level.altar_choice = None
            self._reset_level()
            return

        self.elapsed_time += dt
        # DIFFICULTY_TIERS is sorted ascending by start_time - the last one
        # reached is current, held indefinitely once past the final tier's
        # start_time.
        for tier in settings.DIFFICULTY_TIERS:
            if tier["start_time"] <= self.elapsed_time:
                self.current_tier = tier
        self.level.difficulty_tier = self.current_tier
        self.hud.elapsed_time = self.elapsed_time
        self.hud.difficulty_tier_name = self.current_tier["name"]
        self.hud.difficulty_tier_color = self.current_tier["color"]

        if self.level.altar_phase == "active":
            self.level.altar_buff_timer = max(0.0, self.level.altar_buff_timer - dt)
            if self.level.altar_buff_timer <= 0:
                self.level.altar_phase = "ended"

        # Demon spawning stops entirely once the altar's buff has ended,
        # until the player picks an option back at the altar.
        if self.level.altar_phase != "ended":
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                spawn_interval = self.current_tier["spawn_interval"]
                if self.level.altar_phase == "active":
                    spawn_interval *= settings.ALTAR_SPAWN_INTERVAL_MULTIPLIER
                self.spawn_timer = spawn_interval
                self._spawn_demon()

    def render(self, surface: pygame.Surface) -> None:
        self.level.render(surface, self.camera)
        self.hud.render(surface)
