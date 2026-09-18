import settings
from src.entities.states.BaseEntityState import BaseEntityState
from src.entities.ThrownSword import ThrownSword


class ThrowState(BaseEntityState):
    """Sword throw (W ability) - plays Marze.png's 3-frame throw wind-up
    (timed to fit settings.PLAYER_THROW_DURATION, see Player's "throw"
    animation_defs), spawning the actual src.entities.ThrownSword
    projectile at SPAWN_DELAY, once the throwing motion is far enough
    along to look like it's releasing the sword, rather than on the very
    first frame.
    """

    SPAWN_DELAY = 0.2

    def enter(self) -> None:
        self.entity.change_animation("throw")
        self._elapsed = 0.0
        self._sword_spawned = False
        self.direction = -1 if self.entity.flipped else 1
        self._update_vx()

    def _update_vx(self) -> None:
        """Rooted while grounded (a ground throw shouldn't slide), but
        mid-air keeps normal movement control - same as AttackState.
        """
        if self.entity.on_ground:
            self.entity.vx = 0
            return

        if self.entity.move_direction != 0:
            self.entity.flipped = self.entity.move_direction < 0
        self.entity.vx = self.entity.speed * self.entity.move_direction

    def _spawn_sword(self) -> None:
        entity = self.entity
        offset = entity.width if self.direction > 0 else -ThrownSword.WIDTH
        sword = ThrownSword(
            entity.x + offset,
            entity.y + entity.height / 2 - ThrownSword.HEIGHT / 2,
            self.direction,
            entity.get_damage(settings.PLAYER_THROW_DAMAGE),
            entity,
            entity.level,
        )
        entity.level.entities.append(sword)
        settings.SOUNDS["shadow_throw"].play()

    def update(self, dt: float) -> None:
        # Dropped, not buffered - see AttackState.update's identical guard.
        self.entity.dash_requested = False
        self.entity.attack_requested = False
        self.entity.throw_requested = False
        self.entity.jump_requested = False
        self.entity.rage_requested = False

        self._update_vx()
        self._elapsed += dt

        if not self._sword_spawned and self._elapsed >= self.SPAWN_DELAY:
            self._sword_spawned = True
            self._spawn_sword()

        if self._elapsed >= settings.PLAYER_THROW_DURATION:
            self.entity.change_state("playing")
