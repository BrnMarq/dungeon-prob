import settings
from src.entities.states.BaseEntityState import BaseEntityState


class DeathState(BaseEntityState):
    """The guardian's death, entered from BossReaper.take_damage once its
    hp hits 0.

    boss-reaper.png has no death row, so the guardian stops drawing
    itself entirely and plays assets/graphics/boss/disappear.png in its
    place - see BossReaper.dying/BossReaper.render, which is what
    actually swaps the texture. When that finishes, the guardian marks
    itself dead (src.map.Level.update drops it) and sets
    level.boss_defeated, which src.states.PlayState.update reads the same
    frame to hand the run to VictoryState.
    """

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.vy = 0
        self.entity.dying = True
        self.entity.disappear_frame_index = 0

        self._frame_timer = 0.0
        self._frame_count = len(settings.FRAMES["boss_disappear"])

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self.entity.vy = 0

        self._frame_timer += dt
        if self._frame_timer < settings.BOSS_DISAPPEAR_FRAME_INTERVAL:
            return

        self._frame_timer -= settings.BOSS_DISAPPEAR_FRAME_INTERVAL
        self.entity.disappear_frame_index += 1

        if self.entity.disappear_frame_index >= self._frame_count:
            self.entity.is_dead = True
            self.entity.level.boss_defeated = True
