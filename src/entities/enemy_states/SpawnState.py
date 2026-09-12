from src.entities.states.BaseEntityState import BaseEntityState


class SpawnState(BaseEntityState):
    """Plays once right after the demon is created (see SmallDemon.__init__)
    before it starts acting - holds it in place for the animation's natural
    duration, then hands off to FollowState/IdleState same as before this
    existed.
    """

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.change_animation("spawn")
        animation = self.entity.animations["spawn"]
        self._duration = animation.size * animation.interval
        self._elapsed = 0.0

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self._elapsed += dt

        if self._elapsed >= self._duration:
            self.entity.change_state(
                "follow" if self.entity.target is not None else "idle"
            )
