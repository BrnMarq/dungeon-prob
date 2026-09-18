from typing import Any, List, Optional

import pygame

from gale.tilemap import CollisionType, collision_type_at, load_tiled_map

import settings
from src import debug
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

    def ground_row(self, col: int, layer_name: str = "ground") -> Optional[int]:
        """
        :returns: The first row in col whose layer_name tile is solid or a
        platform (see gale.tilemap.CollisionType), or None if col has no
        collidable tile at all - for spawning something standing on ground.
        """
        for row in range(self.tilemap.rows):
            if collision_type_at(self.tilemap, layer_name, row, col) != CollisionType.NONE:
                return row
        return None

    def update(self, dt: float) -> None:
        for entity in self.entities:
            entity.update(dt)

        self.entities = [entity for entity in self.entities if not entity.is_dead]

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        self.background.render(surface, camera)
        self.tilemap.render(surface, camera)
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
