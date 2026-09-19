from typing import Any, Dict, Optional, TypeVar

import pygame

import settings
from src import render
from src.entities.DamageNumber import DamageNumber
from src.entities import mixins
from src.entities.Entity import Entity
from src.entities.boss_states import (
    AppearState,
    DeathState,
    FloatState,
    LongSlashState,
    MagicState,
    SwipeState,
    TeleportState,
)


class BossReaper(Entity):
    """The forest zone's guardian, "The Reaper" (assets/graphics/boss/
    boss-reaper.png). Summoned by pressing "interact" at the altar once
    its buff has ended (src.entities.Altar's "ended" phase), and beating
    it - not reaching the altar - is what now ends the run: DeathState
    sets level.boss_defeated, which src.states.PlayState.update turns
    into VictoryState.

    Unlike every other Entity it floats: update() below deliberately does
    not call Entity.update, so no gravity is applied and no tile
    collision is resolved - it drifts freely through the level, clamped
    only to the map's own bounds. Its states (src.entities.boss_states)
    drive vx/vy directly.

    It also has no hurt animation to play (boss-reaper.png has no such
    row), so take_damage never interrupts what it is doing - a hit
    registers as a damage number and nothing more, which is a large part
    of why it is hard: unlike a SmallDemon it cannot be stun-locked out
    of a wind-up.
    """

    # Hurtbox, sized to the reaper's body rather than the scythe it holds
    # out to one side - see settings.BOSS_WIDTH/BOSS_HEIGHT.
    WIDTH = settings.BOSS_WIDTH
    HEIGHT = settings.BOSS_HEIGHT

    # The overhead bar src.map.Level.render draws for ordinary enemies is
    # deliberately off here - the guardian gets the full-width bar across
    # the top of the screen instead (src/ui/boss_health_bar.py).
    SHOW_HEALTH_BAR = False

    def __init__(
        self,
        x: float,
        y: float,
        level: TypeVar("Level"),
        target: Optional[Any] = None,
        hp_multiplier: float = 1.0,
        damage_multiplier: float = 1.0,
    ) -> None:
        super().__init__(
            x,
            y,
            self.WIDTH,
            self.HEIGHT,
            "boss_reaper",
            level,
            states={
                "appear": lambda sm: AppearState(self, sm),
                "float": lambda sm: FloatState(self, sm),
                "magic": lambda sm: MagicState(self, sm),
                "teleport": lambda sm: TeleportState(self, sm),
                "swipe": lambda sm: SwipeState(self, sm),
                "long_slash": lambda sm: LongSlashState(self, sm),
                "death": lambda sm: DeathState(self, sm),
            },
            animation_defs={
                "idle": {
                    "frames": list(range(0, 4)),
                    "interval": settings.BOSS_IDLE_FRAME_INTERVAL,
                },
                "magic": {
                    "frames": list(range(12, 15)),
                    "interval": settings.BOSS_MAGIC_FRAME_INTERVAL,
                    "loops": 1,
                },
                # The same three frames forward (vanishing) and backward
                # (arriving) - see boss_states.TeleportState.
                "teleport_out": {
                    "frames": list(range(24, 27)),
                    "interval": settings.BOSS_TELEPORT_FRAME_INTERVAL,
                    "loops": 1,
                },
                "teleport_in": {
                    "frames": list(range(26, 23, -1)),
                    "interval": settings.BOSS_TELEPORT_FRAME_INTERVAL,
                    "loops": 1,
                },
                "swipe": {
                    "frames": list(range(36, 45)),
                    "interval": settings.BOSS_SWIPE_FRAME_INTERVAL,
                    "loops": 1,
                },
                "long_slash": {
                    "frames": list(range(60, 72)),
                    "interval": settings.BOSS_LONG_FRAME_INTERVAL,
                    "loops": 1,
                },
            },
        )
        # boss-reaper.png's art sits inset in its padded 144x128 cell
        # (idle frames' opaque pixels span x 30-93, y 27-110) - this
        # centers that art horizontally on the hurtbox and lines its
        # bottom up with the hurtbox's own, same measurement approach as
        # Marze.png/small-demon.png's offsets.
        self.sprite_offset = (42, 38)

        # Scaled once at spawn time by the current difficulty tier, the
        # same way a SmallDemon's are (see PlayState._spawn_boss) - a
        # longer run means a harder guardian.
        self.max_hp = round(settings.BOSS_MAX_HP * hp_multiplier)
        self.hp = self.max_hp
        self.magic_damage = round(settings.BOSS_MAGIC_DAMAGE * damage_multiplier)
        self.swipe_damage = round(settings.BOSS_SWIPE_DAMAGE * damage_multiplier)
        self.long_damage = round(settings.BOSS_LONG_DAMAGE * damage_multiplier)

        self.target = target
        # Which attack id is mid-swing, for the debug-hitbox overlay
        # (get_attack_hitbox_rect) - set/cleared by boss_states.
        # SwingState, None the rest of the time.
        self.attacking: Optional[str] = None
        # The last attack picked, so FloatState can avoid repeating it.
        self.last_attack: Optional[str] = None
        # Set by boss_states.DeathState - swaps render() over to
        # assets/graphics/boss/disappear.png, which has its own frame
        # counter since it isn't a row of the guardian's own sheet.
        self.dying = False
        self.disappear_frame_index = 0

        self.change_state("appear")

    def face_target(self) -> None:
        """Turns to face self.target - the direction every attack hitbox
        (and the slash sprite drawn over it) is built from.

        NOTE the direction of this test: boss-reaper.png is drawn facing
        LEFT (the hood's opening and the single red eye are on the art's
        left side, and the scythe hangs to the left), unlike Marze.png
        and small-demon.png, which face right. So self.flipped is what
        makes the guardian face RIGHT, and it is set when the target is
        to the right - the opposite of what every other entity here does.
        assets/graphics/boss/slash-effect-norm.png and -wide.png are
        drawn swinging left to match, so they take this same flag as-is
        (see boss_states.SwingState).
        """
        if self.target is None:
            return
        self.flipped = (
            self.target.get_collision_rect().centerx
            > self.get_collision_rect().centerx
        )

    def horizontal_distance_to_target(self) -> float:
        """
        :returns: Horizontal distance, center to center, to self.target -
            what FloatState weights its attack choice by. A very large
            number when there is no target, so nothing reads as "in
            range".
        """
        if self.target is None:
            return float("inf")
        return abs(
            self.target.get_collision_rect().centerx
            - self.get_collision_rect().centerx
        )

    def attack_hitbox_rect(self, attack_id: str) -> pygame.Rect:
        """The world-space rect an attack lands against - the strip past
        the guardian's own hurtbox on the side it currently faces, sized
        per attack (settings.BOSS_SWIPE_HIT_* / BOSS_LONG_HIT_*) to
        roughly cover the slash sprite that attack draws, and centered
        vertically on the hurtbox so it reaches the player hovering
        below.

        Single source of truth for all three consumers - where the damage
        lands, where the slash sprite is centered (boss_states.
        SwingState._land_hit), and what the 'h' debug overlay draws.
        """
        if attack_id == "long_slash":
            width = settings.BOSS_LONG_HIT_WIDTH
            height = settings.BOSS_LONG_HIT_HEIGHT
        else:
            width = settings.BOSS_SWIPE_HIT_WIDTH
            height = settings.BOSS_SWIPE_HIT_HEIGHT

        # self.flipped means facing RIGHT here, not left - see
        # face_target's note on the art's native direction.
        own = self.get_collision_rect()
        x = own.right if self.flipped else own.left - width
        return pygame.Rect(x, own.centery - height / 2, width, height)

    def get_attack_hitbox_rect(self) -> Optional[pygame.Rect]:
        """Debug-overlay hook (src/debug.py, src/map/Level.py) - only
        exposed while actually mid-swing, same as SmallDemon's/Player's.
        """
        if self.attacking is None:
            return None
        return self.attack_hitbox_rect(self.attacking)

    def take_damage(self, amount: int) -> None:
        """Reacts to incoming damage - see src.entities.player_states.
        AttackState._land_hit. There is no stagger: the guardian keeps
        doing whatever it was doing (it has no hurt animation), so it
        cannot be stun-locked out of a wind-up the way a SmallDemon can.

        Guarded on hp<=0 so hits landing during the death animation don't
        restart it or pay out its reward twice.
        """
        if self.hp <= 0:
            return

        self.hp = max(0, self.hp - amount)
        self.level.entities.append(
            DamageNumber(self.x + self.width / 2, self.y, amount)
        )

        if self.hp <= 0:
            self.change_state("death")
            self._grant_rewards()

    def _grant_rewards(self) -> None:
        """The guardian's kill payout - a SmallDemon's, multiplied up by
        its own hp ratio to the demon's, so finally landing the kill is
        worth something on the victory screen rather than reading as one
        more demon.
        """
        target = self.target
        if target is None:
            return

        if hasattr(target, "register_kill"):
            target.register_kill()
        if not hasattr(target, "grant_gold"):
            return

        multiplier = self.level.difficulty_tier["reward_multiplier"] * (
            settings.BOSS_MAX_HP / settings.DEMON_MAX_HP
        )
        target.grant_gold(round(settings.DEMON_BASE_GOLD_REWARD * multiplier))
        target.grant_xp(round(settings.DEMON_BASE_XP_REWARD * multiplier))

    def to_save_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "magic_damage": self.magic_damage,
            "swipe_damage": self.swipe_damage,
            "long_damage": self.long_damage,
        }

    def apply_save_dict(self, data: Dict[str, Any]) -> None:
        """Overlays a to_save_dict() snapshot onto an already-constructed
        BossReaper (see PlayState._load_from_save_data) - a reloaded
        guardian replays its entrance from "appear" rather than resuming
        mid-attack, which is both simpler and fairer than dropping the
        player straight back into a wind-up.
        """
        self.hp = data["hp"]
        self.max_hp = data["max_hp"]
        self.magic_damage = data["magic_damage"]
        self.swipe_damage = data["swipe_damage"]
        self.long_damage = data["long_damage"]

    def update(self, dt: float) -> None:
        """Deliberately does NOT call Entity.update - the guardian floats,
        so it takes neither gravity nor tile collision, and its states
        drive vx/vy directly. Only the map's own bounds constrain it.
        """
        self.state_machine.update(dt)
        mixins.AnimatedMixin.update(self, dt)

        self.x += self.vx * dt
        self.y += self.vy * dt

        self.x = max(0, min(self.tilemap.pixel_width - self.width, self.x))
        self.y = max(0, min(self.tilemap.pixel_height - self.height, self.y))

    def _render_body(self, surface: pygame.Surface, camera: Any) -> None:
        """Like mixins.DrawableMixin.render, but with a sprite_offset
        that mirrors along with the sprite.

        The guardian's art sits off-centre in its own 144px-wide cell
        (the idle frames' opaque pixels span x 30-93, left of the cell's
        middle), so flipping the frame moves the body 20px across the
        cell. A single fixed offset therefore only lines the body up with
        the hurtbox one way round - facing the other way it drew ~20px
        off, and the guardian appeared to jump sideways every time it
        turned. Mirroring the offset with the frame keeps the body on its
        hurtbox in both directions, to within the half-pixel the art's
        odd width costs.
        """
        image = render.sprite(self.texture_id, self.frame_index, self.flipped)
        frame = settings.FRAMES[self.texture_id][self.frame_index]

        offset_x, offset_y = self.sprite_offset
        if self.flipped:
            offset_x = frame.width - offset_x - self.width

        dest = camera.apply(
            pygame.Rect(self.x - offset_x, self.y - offset_y, self.width, self.height)
        )
        render.blit(surface, image, dest)

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        """The guardian's own sheet normally; assets/graphics/boss/
        disappear.png once DeathState takes over (boss-reaper.png has no
        death row), centered on the hurtbox rather than offset like the
        main sheet, since it is a different cell size entirely.
        """
        if not self.dying:
            self._render_body(surface, camera)
            return

        frame_index = min(
            self.disappear_frame_index, len(settings.FRAMES["boss_disappear"]) - 1
        )
        frame = settings.FRAMES["boss_disappear"][frame_index]
        image = render.sprite("boss_disappear", frame_index, self.flipped)

        own = self.get_collision_rect()
        dest = camera.apply(
            pygame.Rect(
                own.centerx - frame.width / 2,
                own.bottom - frame.height,
                frame.width,
                frame.height,
            )
        )
        render.blit(surface, image, dest)
