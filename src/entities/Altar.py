"""
A landmark spawned at a random point from the map's "altars" Tiled
object layer (see src.states.PlayState._spawn_altar - only one altar
exists per map at a time, unlike chests). Duck-typed like src.entities.
Chest (update/render/is_dead, plus get_collision_rect).

Its whole lifecycle is driven off src.map.Level.altar_phase rather than
local flags, since src.states.PlayState (spawn gating/rate, the run-wide
buff countdown) and Player.render (the on-screen countdown) both need to
read/react to the same phase, and a level reset (PlayState._reset_level)
replaces this altar object entirely - the phase has to survive that:

- "inactive": dormant (frame 0). Touching it and pressing "interact"
  fully heals the player, moves to "activating", and starts the wind-up
  animation.
- "activating": plays altars.png's remaining 3 frames
  (ALTAR_ACTIVATE_FRAME_INTERVAL apart), then moves to "active" and
  starts settings.ALTAR_BUFF_DURATION seconds of PlayState's spawn-rate
  buff.
- "active": buff counting down (frozen on the final frame); not
  interactable. PlayState flips this to "ended" once the timer runs out,
  at which point it also stops spawning demons entirely.
- "ended": interactable again - "interact" sets level.altar_choice to
  "final_level", which summons the zone guardian (src.entities.
  BossReaper) rather than ending the run outright: beating it is what
  now reaches VictoryState. "reset" sets it to
  "reset" (PlayState._reset_level regenerates the map, spawns a fresh
  altar back at "inactive", but leaves run time/difficulty/player stats
  alone).
"""

from typing import Any, TypeVar

import pygame

import settings
from src import render
from src.audio import play_music
from src.ui import interact_prompt

_ACTIVATE_FRAME_COUNT = 3  # altars.png frames 1-3, played after frame 0 (dormant)
_OUTLINE_COLOR = pygame.Color(255, 255, 255)
_OUTLINE_OFFSETS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PROMPT_GAP = 6


class Altar:
    WIDTH = 80
    HEIGHT = 80
    # altars.png's actual art sits inset within its padded 80x80 cell
    # (transparent margin on every side, same reason Marze.png/
    # small-demon.png need their own sprite_offset) - measured from the
    # sprite's alpha channel, consistent across all 4 frames: opaque
    # pixels span x 13-77, y 15(ish)-68. Used to anchor a spawn point to
    # where the art actually stands, not the cell's raw edges.
    ART_BOTTOM = 68
    ART_CENTER_X = 45

    @classmethod
    def spawn_position(cls, ground_center_x: float, ground_surface_y: float) -> tuple:
        """Top-left (x, y) so the art's own feet/center - not the padded
        cell's edges - land on (ground_center_x, ground_surface_y).
        """
        return (
            ground_center_x - cls.ART_CENTER_X,
            ground_surface_y - cls.ART_BOTTOM,
        )

    def __init__(
        self,
        x: float,
        y: float,
        player: TypeVar("Player"),
        level: TypeVar("Level"),
    ) -> None:
        self.x = x
        self.y = y
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.player = player
        self.level = level
        self.is_dead = False

        self.frame_index = 0
        self._activate_anim_timer = 0.0

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def can_interact(self) -> bool:
        # Nothing to do at the altar once the guardian it summoned is on
        # the field - the run is decided by that fight now, so neither
        # option (summon again, reset the level) may be taken mid-fight.
        if self.level.boss_active:
            return False
        return self.level.altar_phase in (
            "inactive",
            "ended",
        ) and self.get_collision_rect().colliderect(self.player.get_collision_rect())

    def update(self, dt: float) -> None:
        phase = self.level.altar_phase

        if phase == "activating":
            self._activate_anim_timer += dt
            self.frame_index = 1 + min(
                _ACTIVATE_FRAME_COUNT - 1,
                int(self._activate_anim_timer / settings.ALTAR_ACTIVATE_FRAME_INTERVAL),
            )
            if self.frame_index >= _ACTIVATE_FRAME_COUNT:
                self.level.altar_phase = "active"
                self.level.altar_buff_timer = settings.ALTAR_BUFF_DURATION
            return

        if phase == "active":
            return

        if not self.get_collision_rect().colliderect(self.player.get_collision_rect()):
            return

        if phase == "inactive":
            if not self.player.interact_requested:
                return
            self.player.interact_requested = False
            self.level.altar_phase = "activating"
            self._activate_anim_timer = 0.0
            self.player.heal(self.player.max_hp)
            play_music("altar_activation")
            return

        if phase == "ended":
            if self.level.boss_active:
                return
            if self.player.interact_requested:
                self.player.interact_requested = False
                self.level.altar_choice = "final_level"
            elif self.player.reset_requested:
                self.player.reset_requested = False
                self.level.altar_choice = "reset"

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        image = render.sprite("altars", self.frame_index)

        dest = camera.apply(pygame.Rect(self.x, self.y, self.width, self.height))

        if self.can_interact():
            outline = render.outline("altars", self.frame_index, _OUTLINE_COLOR)
            for dx, dy in _OUTLINE_OFFSETS:
                render.blit(surface, outline, dest.move(dx, dy))

        render.blit(surface, image, dest)

        if self.can_interact():
            if self.level.altar_phase == "inactive":
                prompts = [("interact", "Activate")]
            else:
                prompts = [
                    ("interact", "Summon Guardian"),
                    ("reset", "Reset Level"),
                ]
            interact_prompt.render(surface, dest.centerx, dest.top - _PROMPT_GAP, prompts)
