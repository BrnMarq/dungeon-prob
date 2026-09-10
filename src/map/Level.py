from typing import Any, List

import pygame

from gale.tilemap import load_tiled_map


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

    def update(self, dt: float) -> None:
        for entity in self.entities:
            entity.update(dt)

        self.entities = [entity for entity in self.entities if not entity.is_dead]

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        self.tilemap.render(surface, camera)
        for entity in self.entities:
            entity.render(surface, camera)
