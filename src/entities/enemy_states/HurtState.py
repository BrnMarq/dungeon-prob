from src.entities.states.BaseEntityState import BaseEntityState


class HurtState(BaseEntityState):
    """Brief stagger after taking damage (see SmallDemon.take_damage) -
    interrupts whatever the demon was doing (chasing, winding up an
    attack), then resumes chasing its target, or goes idle if it lost one
    in the meantime.
    """

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.change_animation("hurt")
        animation = self.entity.animations["hurt"]
        self._duration = animation.size * animation.interval
        self._elapsed = 0.0

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self._elapsed += dt

        if self._elapsed >= self._duration:
            self.entity.change_state(
                "follow" if self.entity.target is not None else "idle"
            )
