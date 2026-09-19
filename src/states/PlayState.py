import random
from typing import Any, Dict, Optional, Tuple

import pygame

from gale.camera import Camera
from gale.input_handler import InputData

import settings
from src.audio import play_music
from src.entities.Altar import Altar
from src.entities.BossReaper import BossReaper
from src.entities.Chest import Chest
from src.entities.Decoration import Decoration
from src.entities.Player import Player
from src.entities.SmallDemon import SmallDemon
from src.items.Pickup import Pickup
from src.map.Level import Level
from src.states.BaseState import BaseState
from src.ui import boss_health_bar
from src.ui.HUD import HUD


# How far to one side of the player the guardian floats in when summoned
# (src.states.PlayState._spawn_boss) - inside the camera's own half-
# screen reach either way, so its entrance is always on screen.
BOSS_SPAWN_DISTANCE = 100


class PlayState(BaseState):
    def enter(
        self,
        *args: Tuple[Any],
        save_data: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        play_music("playing")

        self.level = Level(settings.TILEMAPS['forest'])

        if save_data is not None:
            self._load_from_save_data(save_data)
            return

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
        # The zone guardian, once summoned at the altar - None for the
        # whole run up to that point (see _spawn_boss).
        self.boss = None
        self._spawn_chests()
        self._spawn_altar()

        # --- DEBUG (boss testing) - TEMPORARY, delete this block. ---------
        # See settings.DEBUG_START_WITH_BOSS. Runs last so everything
        # _spawn_boss reads (the player, the camera, the difficulty tier,
        # self.boss) already exists.
        if settings.DEBUG_START_WITH_BOSS:
            self._spawn_boss()
        # --- end DEBUG (boss testing) -------------------------------------

    def get_save_data(self) -> Dict[str, Any]:
        """Everything needed to fully reconstruct this run - see
        _load_from_save_data. Called by src.states.PauseMenuState's
        Save option.
        """
        demons = []
        chests = []
        pickups = []
        altar_pos = None
        boss = None

        for entity in self.level.entities:
            if isinstance(entity, SmallDemon):
                demons.append(entity.to_save_dict())
            elif isinstance(entity, Chest):
                chests.append(entity.to_save_dict())
            elif isinstance(entity, Pickup):
                pickups.append(entity.to_save_dict())
            elif isinstance(entity, Altar):
                altar_pos = [entity.x, entity.y]
            elif isinstance(entity, BossReaper):
                boss = entity.to_save_dict()

        return {
            "elapsed_time": self.elapsed_time,
            "spawn_center_x": self._spawn_center_x,
            "spawn_ground_y": self._spawn_ground_y,
            "altar_phase": self.level.altar_phase,
            "altar_buff_timer": self.level.altar_buff_timer,
            "altar_pos": altar_pos,
            "player": self.player.to_save_dict(),
            "demons": demons,
            "chests": chests,
            "pickups": pickups,
            "boss": boss,
        }

    def _load_from_save_data(self, data: Dict[str, Any]) -> None:
        """The save_data path through enter() - reconstructs the run
        get_save_data() captured, in place of the normal random-
        generation path (_spawn_player/_spawn_chests/_spawn_altar).
        """
        self._spawn_center_x = data["spawn_center_x"]
        self._spawn_ground_y = data["spawn_ground_y"]

        player_data = data["player"]
        self.player = Player(player_data["x"], player_data["y"], self.level)
        self.player.apply_save_dict(player_data)
        self.level.entities.append(self.player)
        self._spawn_pillars()

        self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
        self.camera.bounds = self.level.get_rect()
        self.camera.follow(self.player, rate=settings.CAMERA_FOLLOW_RATE)
        self.camera.x, self.camera.y = self.player.x, self.player.y
        self.camera.update(0)

        self.spawn_timer = 0.0
        self.elapsed_time = data["elapsed_time"]
        self.current_tier = settings.DIFFICULTY_TIERS[0]
        for tier in settings.DIFFICULTY_TIERS:
            if tier["start_time"] <= self.elapsed_time:
                self.current_tier = tier

        self.hud = HUD(self.player)
        self.boss = None

        self.level.altar_phase = data["altar_phase"]
        self.level.altar_buff_timer = data["altar_buff_timer"]

        for demon_data in data["demons"]:
            demon = SmallDemon(
                demon_data["x"], demon_data["y"], self.level, target=self.player
            )
            demon.apply_save_dict(demon_data)
            demon.change_state("follow")
            self.level.entities.append(demon)

        for chest_data in data["chests"]:
            chest = Chest(chest_data["x"], chest_data["y"], self.player, self.level)
            chest.apply_save_dict(chest_data)
            self.level.entities.append(chest)

        for pickup_data in data["pickups"]:
            self.level.entities.append(
                Pickup(
                    pickup_data["x"],
                    pickup_data["base_y"],
                    pickup_data["item_id"],
                    self.player,
                    self.level,
                )
            )

        if data["altar_pos"] is not None:
            x, y = data["altar_pos"]
            altar = Altar(x, y, self.player, self.level)
            altar.frame_index = 0 if self.level.altar_phase == "inactive" else 3
            self.level.entities.append(altar)

        # Saves made before the guardian existed (and every save taken
        # outside a boss fight) have no "boss" key/value at all.
        boss_data = data.get("boss")
        if boss_data is not None:
            self.boss = BossReaper(
                boss_data["x"], boss_data["y"], self.level, target=self.player
            )
            self.boss.apply_save_dict(boss_data)
            self.level.entities.append(self.boss)
            self.level.boss_active = True

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
        """Spawns one demon on a standable tile that is actually on
        screen, to either side of the player.

        This used to roll a random column MIN..MAX tiles away and call
        Level.ground_row on it, which only ever reports a column's
        *topmost* platform - on this map that is regularly a ledge dozens
        of rows above the player, so demons appeared out of view above
        him and never on his sides. Instead every standable surface in
        the candidate columns (Level.surface_rows) is checked against the
        camera's visible rect, and the two sides are drawn from evenly so
        one side can't starve.
        """
        position = self._pick_demon_spawn()
        if position is None:
            return

        spawn_x, spawn_y = position
        demon = SmallDemon(
            spawn_x,
            spawn_y,
            self.level,
            target=self.player,
            hp_multiplier=self.current_tier["enemy_hp_multiplier"],
            damage_multiplier=self.current_tier["enemy_damage_multiplier"],
        )
        self.level.entities.append(demon)

    def _visible_rect(self) -> pygame.Rect:
        """
        :returns: The world-space rect the camera is currently showing,
            inset by DEMON_SPAWN_VIEW_MARGIN so a spawn that only just
            fits doesn't end up flush against the screen edge.
        """
        offset_x, offset_y = self.camera.offset
        view = pygame.Rect(
            round(offset_x),
            round(offset_y),
            round(settings.VIRTUAL_WIDTH / self.camera.zoom),
            round(settings.VIRTUAL_HEIGHT / self.camera.zoom),
        )
        margin = settings.DEMON_SPAWN_VIEW_MARGIN
        return view.inflate(-2 * margin, -2 * margin)

    def _pick_demon_spawn(self) -> Optional[Tuple[float, float]]:
        """
        :returns: The top-left world position for a new demon, or None
            when nothing suitable exists this tick (e.g. the player is
            hemmed in by chasms on both sides).

        Candidates are every standable surface (Level.surface_rows) in
        the columns DEMON_SPAWN_MIN/MAX_DISTANCE_TILES away on either
        side whose demon-sized rect fits fully inside the visible rect.
        Surfaces within DEMON_SPAWN_MAX_HEIGHT_DIFF_TILES of the player's
        own feet are preferred - those read as "next to him" and are
        reachable on foot - and the ones merely on screen are only used
        when no such surface exists. Falling back further, to the first
        ground at or below the player's row (rather than the map's
        topmost platform), keeps a spawn tick from silently doing nothing
        in a spot the camera can't cover.
        """
        tile_width = self.level.tilemap.tile_width
        tile_height = self.level.tilemap.tile_height
        cols = self.level.tilemap.cols

        player_col = int(self.player.x // tile_width)
        player_row = int((self.player.y + Player.HEIGHT) // tile_height)
        view = self._visible_rect()

        # direction -> positions, kept apart so each side is equally
        # likely no matter how many standable tiles it happens to offer.
        nearby: Dict[int, list] = {-1: [], 1: []}
        on_screen: Dict[int, list] = {-1: [], 1: []}

        for distance in range(
            settings.DEMON_SPAWN_MIN_DISTANCE_TILES,
            settings.DEMON_SPAWN_MAX_DISTANCE_TILES + 1,
        ):
            for direction in (-1, 1):
                col = player_col + direction * distance
                if not 0 <= col < cols:
                    continue
                x = col * tile_width
                for row in self.level.surface_rows(col):
                    y = row * tile_height - SmallDemon.HEIGHT
                    rect = pygame.Rect(x, y, SmallDemon.WIDTH, SmallDemon.HEIGHT)
                    if not view.contains(rect):
                        continue
                    if (
                        abs(row - player_row)
                        <= settings.DEMON_SPAWN_MAX_HEIGHT_DIFF_TILES
                    ):
                        nearby[direction].append((x, y))
                    else:
                        on_screen[direction].append((x, y))

        for buckets in (nearby, on_screen):
            sides = [positions for positions in buckets.values() if positions]
            if sides:
                return random.choice(random.choice(sides))

        return self._fallback_demon_spawn(player_col, player_row)

    def _fallback_demon_spawn(
        self, player_col: int, player_row: int
    ) -> Optional[Tuple[float, float]]:
        """Off-screen last resort: the old random-column roll, but
        scanning down from the player's own row so the demon lands on the
        platform level with him rather than the column's topmost one.
        """
        tile_width = self.level.tilemap.tile_width
        for _ in range(settings.DEMON_SPAWN_MAX_ATTEMPTS):
            distance = random.randint(
                settings.DEMON_SPAWN_MIN_DISTANCE_TILES,
                settings.DEMON_SPAWN_MAX_DISTANCE_TILES,
            )
            direction = random.choice((-1, 1))
            col = max(
                0, min(self.level.tilemap.cols - 1, player_col + direction * distance)
            )
            row = self.level.ground_row(col, start_row=max(0, player_row - 1))
            if row is not None:
                return (
                    col * tile_width,
                    row * self.level.tilemap.tile_height - SmallDemon.HEIGHT,
                )
        return None

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

    def _spawn_boss(self) -> None:
        """Summons the zone guardian (src.entities.BossReaper), chosen at
        the altar once its buff has ended (level.altar_choice ==
        "final_level"). That choice used to jump straight to
        VictoryState; now the guardian is what stands between the player
        and it.

        It floats in beside the player rather than on the altar itself -
        far enough to read as an entrance and to leave room to react,
        close enough to stay on screen (the camera shows half of
        VIRTUAL_WIDTH either side), clamped to the map's own width. Its
        hp/damage are scaled by the current difficulty tier exactly like
        a SmallDemon's, so a longer run means a harder guardian.
        """
        player_rect = self.player.get_collision_rect()
        side = 1 if player_rect.centerx < self.level.tilemap.pixel_width / 2 else -1

        x = player_rect.centerx + side * BOSS_SPAWN_DISTANCE - BossReaper.WIDTH / 2
        x = max(0, min(self.level.tilemap.pixel_width - BossReaper.WIDTH, x))
        y = max(
            0,
            player_rect.bottom - settings.BOSS_HOVER_HEIGHT - BossReaper.HEIGHT,
        )

        self.boss = BossReaper(
            x,
            y,
            self.level,
            target=self.player,
            hp_multiplier=self.current_tier["enemy_hp_multiplier"],
            damage_multiplier=self.current_tier["enemy_damage_multiplier"],
        )
        self.level.entities.append(self.boss)
        self.level.boss_active = True

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
        # A reset can only be chosen before the guardian is summoned, but
        # clearing these keeps "fresh level" honest in one place rather
        # than relying on that.
        self.boss = None
        self.level.boss_active = False
        self.level.boss_defeated = False
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

        if self.player.hp <= 0:
            self.state_machine.change("game_over")
            return

        if self.level.boss_defeated:
            self.level.boss_defeated = False
            self.state_machine.change(
                "victory", player=self.player, elapsed_time=self.elapsed_time
            )
            return

        if self.level.altar_choice == "final_level":
            self.level.altar_choice = None
            self._spawn_boss()
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
                play_music("playing")

        # Demon spawning stops entirely once the altar's buff has ended,
        # until the player picks an option back at the altar - and stays
        # off for the guardian fight itself, which is meant to be won
        # one-on-one rather than while a horde piles in.
        if self.level.altar_phase != "ended" and not self.level.boss_active:
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
        if self.boss is not None and not self.boss.is_dead:
            boss_health_bar.render(surface, self.boss)
