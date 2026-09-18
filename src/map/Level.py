from typing import Any, List, Optional

import pygame

from gale.tilemap import CollisionType, collision_type_at, load_tiled_map

import settings
from src import debug, render
from src.map.Background import ParallaxBackground
from src.ui.health_bar import render_health_bar


class Level:
    """Loads a Tiled JSON map and owns the entities living on it. Subclasses
    (or callers) are expected to populate self.entities - e.g. from the
    tilemap's object layers - and to add zone-specific logic like the
    beacon/portal and guardian spawn on top of this scaffold.
    """

    def __init__(self, tilemap_path: str) -> None:
        self.tilemap = load_tiled_map(tilemap_path)
        # The map's tile layers, flattened into one image once here
        # rather than re-blitted tile by tile every frame. TileMap.render
        # culls to the visible range, but that is still ~300 individual
        # per-pixel-alpha blits per frame through pygame's own (slow)
        # blitter; against one cached surface the same frame is a single
        # blit through SDL2's - see src.render.
        self._tilemap_surface = self._prerender_tilemap()
        self.entities: List[Any] = []
        self.background = ParallaxBackground(
            self.get_rect().width, settings.VIRTUAL_WIDTH
        )
        # Current named difficulty tier (settings.DIFFICULTY_TIERS) - scales
        # kill rewards (see src.entities.SmallDemon.take_damage), kept
        # updated by src.states.PlayState.update as play time elapses.
        self.difficulty_tier = settings.DIFFICULTY_TIERS[0]
        # Seconds remaining on the altar's spawn-rate buff (0 outside the
        # "active" phase below) - set by src.entities.Altar on activation,
        # ticked down and acted on by src.states.PlayState.update, and
        # read by Player.render to show the countdown above the player's
        # head.
        self.altar_buff_timer = 0.0
        # The altar's lifecycle - "inactive" (dormant) -> "activating"
        # (wind-up animation) -> "active" (buff running, no spawning
        # changes besides the rate) -> "ended" (buff ran out - demon
        # spawning stops entirely until the player picks an option at the
        # altar). See src.entities.Altar and src.states.PlayState.
        self.altar_phase = "inactive"
        # Set by src.entities.Altar while altar_phase is "ended" -
        # "final_level" or "reset" - and acted on then cleared by
        # src.states.PlayState.update the same frame.
        self.altar_choice = None

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(0, 0, self.tilemap.pixel_width, self.tilemap.pixel_height)

    def ground_row(
        self, col: int, layer_name: str = "ground", start_row: int = 0
    ) -> Optional[int]:
        """
        :param start_row: Row to start scanning downward from - the top
            of the map (0) by default. Pass a spawn point's own row to
            snap to the platform directly beneath it instead of
            whichever platform happens to be topmost in that column -
            this map has several stacked in the same column in places
            (see the vines/climbing content), so scanning from the top
            can land you on a completely different platform than the
            one the point was actually placed on.
        :returns: The first row at or below start_row in col whose
            layer_name tile is solid or a platform (see
            gale.tilemap.CollisionType), or None if nothing collidable is
            found there - for spawning something standing on ground.
        """
        for row in range(start_row, self.tilemap.rows):
            if collision_type_at(self.tilemap, layer_name, row, col) != CollisionType.NONE:
                return row
        return None

    def surface_rows(self, col: int, layer_name: str = "ground") -> List[int]:
        """Every standable surface in a column, not just the topmost one.

        ground_row only ever reports the first collidable tile at or
        below its start_row, which makes it useless for picking *which*
        of a column's several stacked platforms something should spawn
        on (this map stacks them - see the vines/climbing content). A row
        counts as a surface when its own tile is collidable and the tile
        directly above it is not, i.e. there is open space to stand in.

        :returns: Those rows, top to bottom (possibly empty).
        """
        rows: List[int] = []
        for row in range(self.tilemap.rows):
            if collision_type_at(self.tilemap, layer_name, row, col) == CollisionType.NONE:
                continue
            above_is_open = (
                row == 0
                or collision_type_at(self.tilemap, layer_name, row - 1, col)
                == CollisionType.NONE
            )
            if above_is_open:
                rows.append(row)
        return rows

    def update(self, dt: float) -> None:
        for entity in self.entities:
            entity.update(dt)

        self.entities = [entity for entity in self.entities if not entity.is_dead]

    def _prerender_tilemap(self) -> pygame.Surface:
        """
        :returns: Every tile layer drawn, in order, onto one
            pixel_width x pixel_height transparent surface at 1:1 - what
            _render_tilemap then scrolls past the camera.
        """
        surface = pygame.Surface(
            (self.tilemap.pixel_width, self.tilemap.pixel_height), pygame.SRCALPHA
        )
        # camera=None renders the whole map at 1:1 from (0, 0), which is
        # exactly this surface's coordinate system.
        self.tilemap.render(surface)
        return surface.convert_alpha()

    def _render_tilemap(self, surface: pygame.Surface, camera: Any) -> None:
        """Blit the cached tilemap image, scrolled by the camera.

        Only correct at zoom 1 (where a tile's on-screen position is
        round(x - offset_x), and x is always a whole number of pixels, so
        offsetting the whole image by round(-offset_x) lands every tile
        on the same pixel the per-tile path would have). Anything else
        falls back to TileMap.render, which handles scaling properly.
        """
        if camera.zoom != 1:
            self.tilemap.render(surface, camera)
            return

        offset_x, offset_y = camera.offset
        render.blit(
            surface, self._tilemap_surface, (round(-offset_x), round(-offset_y))
        )

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        self.background.render(surface, camera)
        self._render_tilemap(surface, camera)
        for entity in self.entities:
            entity.render(surface, camera)
            if getattr(entity, "SHOW_HEALTH_BAR", False):
                render_health_bar(surface, camera, entity)

        if settings.DEBUG_HITBOXES:
            self._render_debug_hitboxes(surface, camera)

    def _render_debug_hitboxes(self, surface: pygame.Surface, camera: Any) -> None:
        for entity in self.entities:
            if hasattr(entity, "get_collision_rect"):
                debug.draw_translucent_rect(
                    surface, camera, entity.get_collision_rect(), settings.DEBUG_HURTBOX_COLOR
                )
            if hasattr(entity, "get_attack_hitbox_rect"):
                hitbox = entity.get_attack_hitbox_rect()
                if hitbox is not None:
                    debug.draw_translucent_rect(
                        surface, camera, hitbox, settings.DEBUG_HITBOX_COLOR
                    )
            if hasattr(entity, "get_rage_hitbox_circle"):
                circle = entity.get_rage_hitbox_circle()
                if circle is not None:
                    center_x, center_y, radius = circle
                    debug.draw_translucent_circle(
                        surface,
                        camera,
                        (center_x, center_y),
                        radius,
                        settings.DEBUG_HITBOX_COLOR,
                    )
