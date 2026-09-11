# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project has no releases yet, so everything lives under **Unreleased**
until the first tagged version.

## [Unreleased]

### Added

- Debug hitbox/hurtbox overlay: `src/debug.py`'s `draw_translucent_rect`,
  drawn from `src.map.Level.render` (gated on `settings.DEBUG_HITBOXES`,
  on by default while combat is being tuned). Every entity with
  `get_collision_rect` (i.e. anything using `CollidableMixin` - `Player`,
  `SmallDemon`) gets a translucent purple hurtbox rectangle; anything with
  a `get_attack_hitbox_rect` method (currently just `SmallDemon`) gets a
  translucent red one on top, but only while actually mid-swing
  (`isinstance(self.state_machine.current, AttackState)`) - not for the
  whole time `FollowState` is range-checking. `settings.DEBUG_HURTBOX_COLOR`/
  `DEBUG_HITBOX_COLOR` are the two new colors - both plain
  `(r, g, b, alpha)` tuples rather than `pygame.Color` since the overlay
  needs real per-pixel alpha (filled onto an `SRCALPHA` surface and
  blitted, since `pygame.draw.rect` ignores alpha on a non-`SRCALPHA`
  destination).
- Enemy attacks now actually damage the player: `AttackState`
  (`src/entities/enemy_states/AttackState.py`) decrements `target.hp` by
  `settings.DEMON_ATTACK_DAMAGE` and spawns a `src/entities/DamageNumber.py`
  popup at the player's position the moment the attack lands - the HP bar
  in `src/ui/HUD.py` picks it up for free since it already reads
  `player.hp` fresh every render. The hit lands `AttackState.HIT_FRAME_INDEX`
  (3) frames into the swing rather than instantly on enter, synced to the
  frame where `small-demon.png`'s attack animation shows the actual sword
  swing/flash. `FollowState` only triggers `AttackState` once the target is
  already in `settings.DEMON_ATTACK_RANGE` - no dodge/miss mechanic exists
  yet, so the attack is guaranteed to connect once it lands.
  `DamageNumber` isn't an `Entity` (no physics needed) but matches the
  same `update`/`render`/`is_dead` interface `Level.entities` expects, so
  it drops into that list like any other entity - rises and self-removes
  after its lifetime. `settings.DAMAGE_NUMBER_COLOR` (purple) and
  `DEMON_ATTACK_DAMAGE` are the two new constants.
- First HUD pass: `src/ui/HUD.py`, drawn in screen space (not through the
  camera) from `PlayState.render()`. Horizontally-centered, bottom-anchored
  block: a level badge, a green HP bar with `current/max` text on it, a blue
  XP-to-next-level bar underneath, and a row of 4 ability-icon slots (native
  32x32) above them - all built on `gale.ui`'s existing `ProgressBar` widget
  plus `gale.text.render_text`, no new widget types needed. All 4 ability
  slots currently repeat the same `marze-abilities.png` icon since only one
  ability exists yet. Text uses pygame's built-in font at size 12 as a
  placeholder - `assets/fonts/` doesn't have a pixel font yet.
- `Player` now carries stats: `level_num`, `hp`/`max_hp`
  (`settings.PLAYER_MAX_HP = 100`), `xp`/`xp_to_next_level`
  (`settings.PLAYER_XP_TO_NEXT_LEVEL = 100`, flat for now - no leveling
  curve designed yet). Named `level_num` rather than `level` since `Entity`
  already uses `self.level` for the map/`Level` reference.
- Player character: `src/entities/Player.py`, driven by a single consolidated
  `PlayingState` (`src/entities/player_states/`) since `Marze.png` is only one
  sprite for now - ground/air movement and variable-height jumping, no
  animation switching yet. Spawns standing on the forest map's ground row and
  is followed by the camera in `PlayState`.
- `src/commands.py`: `Command` classes (`MOVE_LEFT`, `MOVE_RIGHT`, `JUMP`,
  ...) that only record intent on the receiver (`move_direction`,
  `jump_requested`, `jump_held`). Shared by a human-controlled player (via
  `CommandBindings` + `InputHandler`) and, later, AI-controlled monsters
  calling the same commands directly from their own state logic.
- Base entity framework, ported from an earlier reference project
  (`05-super_martian`) and adapted to this project's naming:
  - `src/entities/Entity.py` - base class for anything living on the level's
    tilemap: gravity, tile collision (`gale.tilemap.move_and_collide`), a
    per-entity state machine, and animation playback.
  - `src/entities/mixins/` - `DrawableMixin`, `AnimatedMixin`,
    `CollidableMixin`.
  - `src/entities/states/BaseEntityState.py` - shared base for per-entity
    states (holds the owning entity).
  - `src/map/Level.py` - loads a Tiled JSON map (`gale.tilemap.load_tiled_map`)
    and owns/updates/renders the entities living on it.
- `assets/maps/forest.json` + `assets/graphics/forest.png`: first playable
  tilemap (background + ground layers, solid-tile collision properties).
- `settings.py`: `GRAVITY`, `CAMERA_FOLLOW_RATE`, `PLAYER_SPEED`,
  `JUMP_TAKEOFF_SPEED`, `JUMP_CUT_VELOCITY`, a `TILEMAPS` registry, the
  `marze` texture/frames, and `move_left`/`move_right`/`jump` key bindings.
- `PlayState` now loads the forest `Level`, spawns the `Player`, and renders
  both through a `gale.camera.Camera`.
- First enemy: `src/entities/SmallDemon.py`, using the new
  `assets/graphics/small-demon.png` sheet (800x600, 8x6 grid of 100x100
  cells - idle/run/attack/hurt/dead animations all sliced and registered).
  AI lives in `src/entities/enemy_states/`:
  - `FollowState` - chases `self.target` (the player) horizontally.
  - `AttackState` - triggered once in range; plays the attack animation
    once, pauses idle for `settings.DEMON_ATTACK_COOLDOWN`, then hands back
    to `FollowState`.
  - `IdleState` - fallback for a demon with no target.
  `PlayState` spawns one demon on a random ground tile within camera view of
  the player (3+ tiles away) and passes the player in as its `target`.
- `src/entities/mixins/DrawableMixin.py`: entities can now set
  `sprite_offset` so a frame's art aligns with a hitbox smaller than its raw
  cell - needed because `small-demon.png`'s creature is ~20x22px inside a
  padded 100x100 cell (vs. `Marze.png`'s flush 16x16, `sprite_offset=(0, 0)`).
- `settings.py`: `DEMON_SPEED`, `DEMON_ATTACK_RANGE`, `DEMON_ATTACK_COOLDOWN`,
  and the `small_demon` texture/frames.
- Marze got a real idle animation: `assets/graphics/Marze.png` is now
  128x32 (4 frames, 32x32 each) instead of a single flush 16x16 sprite.
  Player's `idle` animation plays all 4 frames (`interval: 0.2`).

### Changed

- Doubled the virtual resolution (`settings.VIRTUAL_WIDTH/HEIGHT`:
  320x180 → 640x360), window size unchanged - drops the render scale from
  4x to 2x, so the camera now shows twice as much of the map (40 tiles
  wide instead of 20) and every sprite reads proportionally smaller on
  screen. `src/ui/HUD.py`'s own pixel constants (icon size, bar heights,
  margins, font) are doubled to match, so the HUD keeps its current
  on-screen size instead of shrinking along with the world view - the
  ability icon texture (native 32x32) is now scaled 2x once at HUD
  construction to fill its 64x64 slot.
- Player is now rendered/collided at 32x32 (`Player.WIDTH`/`HEIGHT`),
  matching `Marze.png`'s native frame size, rather than downscaling the
  texture 2x to read as 16x16 - reverts that downscale from the previous
  pass now that the bigger size is the intended look.
- `TitleState`, `PauseState`, `GameOverState`, `VictoryState` now forward
  straight to `PlayState` on `enter()` (marked `TODO`), so the game is
  reachable for testing before those screens exist.

### Fixed

- `assets/maps/forest.json` referenced its tileset image via a path that
  escaped the repo entirely (`../../../../../Downloads/Mini Legend Starter
  Bundle/terrains/forest.png`). The tileset now lives in
  `assets/graphics/forest.png` and the map references it as
  `../graphics/forest.png`, so the map no longer depends on a specific
  machine's Downloads folder.
- `DungeonProb.on_input` (`src/Game.py`) handled `quit` but never forwarded
  input to `self.state_machine`, so no state - and nothing inside it, like
  the player - could ever receive input. Added the missing
  `self.state_machine.on_input(...)` call.
- Demon attacks could land on a player who was no longer anywhere near the
  visualized hitbox: `FollowState` decided *whether* to attack from a
  single point-distance check, but `AttackState._land_hit` applied the
  damage `AttackState.HIT_FRAME_INDEX` frames later without re-checking
  position, so a target that walked away during the wind-up still got hit
  (and, separately, `FollowState`'s trigger condition didn't match what
  the debug rect actually drew - a plain `abs(dx) <= DEMON_ATTACK_RANGE`
  point check vs. a rect the size of `SmallDemon.melee_range_rect()`).
  Both now go through that single `melee_range_rect()`/`colliderect()`
  check - `FollowState` to decide when to attack, `AttackState._land_hit`
  to decide whether it still connects - so "when it triggers," "whether it
  lands," and "what the debug overlay shows" always agree.
- `SmallDemon.melee_range_rect()` extended `settings.DEMON_ATTACK_RANGE` on
  both sides of the demon, so it could hit (and show a hitbox for) a
  target directly behind it, not just the one it's facing. Now extends
  the range only on the side `self.flipped` is currently facing.
