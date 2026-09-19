import settings
from src.entities.SlashEffect import SlashEffect
from src.entities.states.BaseEntityState import BaseEntityState


class SwingState(BaseEntityState):
    """Shared behavior for the guardian's two melee attacks - the scythe
    swipe (src.entities.boss_states.SwipeState) and the long sweep
    (LongSlashState). They differ only in which animation row they play,
    which slash sprite they draw, and how hard/far they hit, all of which
    subclasses declare as the class attributes below.

    Both hover in place for the whole swing (the guardian never lunges),
    spawn their slash sprite and land their hit together HIT_FRAME_INDEX
    frames in - matched to where the art actually shows the blade
    sweeping through, the same trick src.entities.enemy_states.
    AttackState uses - and re-check the hitbox at that moment via
    BossReaper.attack_hitbox_rect rather than trusting the range check
    that picked the attack, so walking out of a wind-up genuinely dodges
    it.
    """

    ATTACK_ID: str = ""
    ANIMATION_ID: str = ""
    SLASH_TEXTURE_ID: str = ""
    SLASH_FRAME_INTERVAL: float = 0.0
    HIT_FRAME_INDEX: int = 0
    DAMAGE_ATTRIBUTE: str = ""

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.vy = 0
        self.entity.last_attack = self.ATTACK_ID
        self.entity.face_target()
        self.entity.change_animation(self.ANIMATION_ID)

        animation = self.entity.animations[self.ANIMATION_ID]
        self._duration = animation.size * animation.interval
        self._hit_delay = self.HIT_FRAME_INDEX * animation.interval
        self._elapsed = 0.0
        self._hit_landed = False

    def _land_hit(self) -> None:
        hitbox = self.entity.attack_hitbox_rect(self.ATTACK_ID)

        self.entity.level.entities.append(
            SlashEffect(
                self.SLASH_TEXTURE_ID,
                hitbox.centerx,
                hitbox.centery,
                self.SLASH_FRAME_INTERVAL,
                flipped=self.entity.flipped,
            )
        )
        settings.SOUNDS["demon_attack"].play()

        target = self.entity.target
        if target is None or not hasattr(target, "take_damage"):
            return
        if hitbox.colliderect(target.get_collision_rect()):
            target.take_damage(getattr(self.entity, self.DAMAGE_ATTRIBUTE))

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self.entity.vy = 0
        self._elapsed += dt

        if not self._hit_landed and self._elapsed >= self._hit_delay:
            self._hit_landed = True
            self._land_hit()

        if self._elapsed >= self._duration:
            self.entity.change_state("float")
