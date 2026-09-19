import settings
from src.entities.states.BaseEntityState import BaseEntityState


class TeleportState(BaseEntityState):
    """The guardian's gap closer - boss-reaper.png's 3-frame teleport row
    (frames 24-26) played forward to vanish, then backward to reappear.

    It reappears settings.BOSS_TELEPORT_OFFSET pixels to one side of the
    player (the side it was already on, so it doesn't cross through them)
    at its usual hover height, then goes straight into a swipe rather
    than back to "float" - reappearing and then politely waiting out
    another cooldown would waste the whole point of the move.

    Three phases, tracked by _phase since the wind-up and the arrival are
    the same three frames in opposite directions:
    - "out": vanish animation, still at the old position.
    - "in": repositioned, arrival animation playing.
    - handing off to "swipe" the frame the arrival finishes.
    """

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.vy = 0
        self.entity.last_attack = "teleport"
        self.entity.change_animation("teleport_out")

        animation = self.entity.animations["teleport_out"]
        self._phase_duration = animation.size * animation.interval
        self._elapsed = 0.0
        self._phase = "out"
        settings.SOUNDS["shadow_throw"].play()

    def _reposition(self) -> None:
        """Drops the guardian beside the player - on the side it was
        already on, and clamped to the level's own width so it can never
        materialize outside the map.
        """
        target = self.entity.target
        if target is None:
            return

        target_rect = target.get_collision_rect()
        own_rect = self.entity.get_collision_rect()
        side = -1 if own_rect.centerx < target_rect.centerx else 1

        x = target_rect.centerx + side * settings.BOSS_TELEPORT_OFFSET
        x -= self.entity.width / 2
        self.entity.x = max(
            0,
            min(self.entity.tilemap.pixel_width - self.entity.width, x),
        )
        self.entity.y = (
            target_rect.bottom - settings.BOSS_HOVER_HEIGHT - self.entity.height
        )
        self.entity.face_target()

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self.entity.vy = 0
        self._elapsed += dt

        if self._elapsed < self._phase_duration:
            return

        if self._phase == "out":
            self._phase = "in"
            self._elapsed = 0.0
            self._reposition()
            self.entity.change_animation("teleport_in")
            return

        self.entity.change_state("swipe")
