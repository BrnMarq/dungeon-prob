from typing import Any, List, Optional

import pygame

from gale.tilemap import CollisionType, collision_type_at, load_tiled_map

import settings
from src import debug
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
