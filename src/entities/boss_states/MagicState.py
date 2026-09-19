import settings
from src.entities.BossMagic import BossMagic
from src.entities.states.BaseEntityState import BaseEntityState


class MagicState(BaseEntityState):
    """The guardian's ranged attack - boss-reaper.png's 3-frame cast row
    (frames 12-14), hovering in place.

    The cast itself deals no damage: when the animation finishes it
    spawns a src.entities.BossMagic centered on wherever the player is
    standing at that moment, which telegraphs as a growing ring before
    detonating. That delay, not this animation, is the dodge window - see
    settings.BOSS_MAGIC_TELEGRAPH.
    """

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.vy = 0
        self.entity.last_attack = "magic"
        self.entity.change_animation("magic")

        animation = self.entity.animations["magic"]
        self._duration = animation.size * animation.interval
        self._elapsed = 0.0
        self._cast = False

    def _cast_at_target(self) -> None:
        target = self.entity.target
        if target is None:
            return

        rect = target.get_collision_rect()
        self.entity.level.entities.append(
            BossMagic(
                rect.centerx,
                rect.centery,
                self.entity.magic_damage,
                target,
            )
        )
        settings.SOUNDS["shadow_throw"].play()

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self.entity.vy = 0
        self.entity.face_target()
        self._elapsed += dt

        if not self._cast and self._elapsed >= self._duration:
            self._cast = True
            self._cast_at_target()
            self.entity.change_state("float")
