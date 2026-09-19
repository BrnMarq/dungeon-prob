from src.entities.states.BaseEntityState import BaseEntityState


class AppearState(BaseEntityState):
    """The guardian's entrance, played once right after it is summoned at
    the altar (see src.states.PlayState._spawn_boss).

    boss-reaper.png has no dedicated spawn row, so this reuses the
    teleport row played backward - the same "materializes out of nothing"
    read the teleport's own arrival has - and holds the guardian in place
    until it finishes, giving the player a moment to see what showed up
    before it starts attacking.
    """

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.vy = 0
        self.entity.change_animation("teleport_in")
        animation = self.entity.animations["teleport_in"]
        self._duration = animation.size * animation.interval
        self._elapsed = 0.0

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self.entity.vy = 0
        self.entity.face_target()
        self._elapsed += dt

        if self._elapsed >= self._duration:
            self.entity.change_state("float")
