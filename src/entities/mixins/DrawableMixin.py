from typing import Any

import pygame

from src import render


class DrawableMixin:
    def render(self, surface: pygame.Surface, camera: Any) -> None:
        image = render.sprite(self.texture_id, self.frame_index, self.flipped)

        offset_x, offset_y = self.sprite_offset
        dest = camera.apply(
            pygame.Rect(self.x - offset_x, self.y - offset_y, self.width, self.height)
        )
        render.blit(surface, image, dest)
