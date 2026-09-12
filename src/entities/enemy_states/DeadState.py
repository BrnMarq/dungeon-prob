from src.entities.states.BaseEntityState import BaseEntityState


class DeadState(BaseEntityState):
    """Plays the death animation once, then marks the entity dead so
    src.map.Level.update drops it from the level's entities list.
    """

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.change_animation("dead")
        animation = self.entity.animations["dead"]
        self._duration = animation.size * animation.interval
        self._elapsed = 0.0

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self._elapsed += dt

        if self._elapsed >= self._duration:
            self.entity.is_dead = True
