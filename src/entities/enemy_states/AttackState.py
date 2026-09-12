import settings
from src.entities.states.BaseEntityState import BaseEntityState


class AttackState(BaseEntityState):
    """Plays the attack animation once, then stands idle for
    settings.DEMON_ATTACK_COOLDOWN before FollowState resumes the chase.

    The hit lands HIT_FRAME_INDEX frames into the swing rather than
    instantly on enter, synced to the frame where small-demon.png's attack
    animation actually shows the sword swinging out (a flash effect) -
    see assets/graphics/small-demon.png's attack row (frames 24-30).
    FollowState only transitions here once the target is already in
    settings.DEMON_ATTACK_RANGE, but the target can walk back out of range
    during the wind-up before the hit actually lands - _land_hit re-checks
    entity.melee_range_rect() at that moment rather than trusting the
    range check that triggered this state, so a hit never lands on a
    target that isn't inside the (visualized) hitbox at the time it lands.
    """

    HIT_FRAME_INDEX = 3

    def enter(self) -> None:
        self.entity.vx = 0
        self.entity.change_animation("attack")
        self._elapsed = 0.0
        self._switched_to_idle = False
        self._hit_landed = False

        animation = self.entity.animations["attack"]
        self._attack_duration = animation.size * animation.interval
        self._hit_delay = self.HIT_FRAME_INDEX * animation.interval

    def _land_hit(self) -> None:
        target = self.entity.target
        if target is None:
            return

        if not self.entity.melee_range_rect().colliderect(target.get_collision_rect()):
            return  # target moved out of range during the wind-up - miss

        target.take_damage(settings.DEMON_ATTACK_DAMAGE)

    def update(self, dt: float) -> None:
        self.entity.vx = 0
        self._elapsed += dt

        if not self._hit_landed and self._elapsed >= self._hit_delay:
            self._hit_landed = True
            self._land_hit()

        if not self._switched_to_idle and self._elapsed >= self._attack_duration:
            self.entity.change_animation("idle")
            self._switched_to_idle = True

        if self._elapsed >= self._attack_duration + settings.DEMON_ATTACK_COOLDOWN:
            self.entity.change_state("follow")
