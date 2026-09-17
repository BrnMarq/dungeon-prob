# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/) - while
the major version stays `0`, breaking changes can land in any release.

## [Unreleased] - 2026-09-17

Two more abilities, a full 12-item stackable pickup system, a parallax
background, and a combat VFX pass - built on top of 0.1.0's foundation.

### Added

- Thrown sword ability (`W` / HUD slot 2, `src/entities/player_states/ThrowState.py`
  + `src/entities/ThrownSword.py`, `assets/graphics/dark-sword.png`): plays
  `Marze.png`'s 3-frame throw wind-up, then spawns a projectile that flies
  `settings.SWORD_TRAVEL_DISTANCE` (matching the dash's own speed/duration),
  damaging each enemy it touches at most once while cycling through
  thrown/midair/near_max_travel animations by distance fraction. Lands and
  floats in place (sine-tweened y, looping animation) until the player
  touches it, detonating it - a `gale.particle_system` burst plus
  `SWORD_EXPLOSION_RADIUS` area damage, and refunding the player's dash
  cooldown.
- Rage ability (`R` / HUD slot 4, `src/entities/player_states/RageState.py`):
  an invincible radius burst - plays `Marze.png`'s new row-5 3-frame
  wind-up, holds on the last frame for most of `PLAYER_RAGE_DURATION`, then
  plays it backward as the ability ends. Grants full-duration invincibility
  and lands `PLAYER_RAGE_HITS` hits, evenly spaced, against everything
  within `PLAYER_RAGE_RADIUS` of the player's center.
- Stackable item pickup system: `src/items/Pickup.py` (a `DamageNumber`-style
  duck-typed entity - float-bob idle animation, glowing outline, applies its
  effect via `Player.collect_item` on touch and removes itself) plus
  `src/items/definitions.py`'s `ITEMS` registry mapping each item id to a
  texture id/sprite frame. `Player.item_stacks` (a `Counter`) tracks how many
  of each item has been picked up; `PlayState._spawn_test_items` spawns one
  of every registered item at the end of the map for manual testing.
  Twelve items, each read live off `item_stacks` by the stat it modifies:
  - **Walking cane** - `Player.speed` scaled by `ITEM_SPEED_BONUS`, additive.
  - **Frozen heart** - `ITEM_HP_BONUS` added to `max_hp`/`hp` immediately on
    pickup (the only item with an instant rather than derived effect).
  - **Bloody knife** - `Player.get_damage` scaled by `ITEM_DAMAGE_BONUS`,
    additive; read by melee/throw/rage and the sword's explosion.
  - **Aegis shield** - `Player.take_damage` scales incoming damage by
    `ITEM_RESISTANCE_FACTOR`, compounding (diminishing returns, never 0).
  - **Short daggers** - `Player.attack_duration` scales by
    `ITEM_ATTACK_SPEED_FACTOR`, compounding, floored at
    `ITEM_ATTACK_DURATION_FLOOR` so it can't zero out the swing.
  - **Hunter's hat** - `Player.crit_chance`, linear (`ITEM_CRIT_CHANCE_BONUS`
    per stack, capped at 100%); a successful roll in `get_damage` multiplies
    damage by `ITEM_CRIT_DAMAGE_MULTIPLIER`.
  - **Cat's spirit** - `Player.dodge_chance`, linear
    (`ITEM_DODGE_CHANCE_BONUS`, capped at `ITEM_DODGE_CHANCE_CAP`); a
    successful roll in `take_damage` skips the hit entirely and spawns a
    white "Dodged!" popup instead of a damage number.
  - **Loadstone** - `Player.cooldown_multiplier`, compounding
    (`ITEM_COOLDOWN_REDUCTION_FACTOR`, floored at
    `ITEM_COOLDOWN_REDUCTION_FLOOR`), applied wherever `PlayingState` starts
    the dash/throw/rage cooldown timers.
  - **Blood thirst** - every crit rolled in `get_damage` also shaves
    `ITEM_BLOOD_THIRST_COOLDOWN_REDUCTION * stacks` off all three cooldown
    timers currently counting down (`Player._reduce_cooldowns_on_crit`).
  - **Samurai sword** - `Player.maybe_trigger_samurai_burst`, called after
    every landed hit (melee, thrown sword, rage - including the burst's own
    hits, applied directly so it can't chain into itself): a rare per-stack
    chance (`ITEM_SAMURAI_PROC_CHANCE`, capped at
    `ITEM_SAMURAI_PROC_CHANCE_CAP`) of an extra rage-style AOE burst
    centered on the player.
  - **Jimbo** - flat, non-stacking `ITEM_JIMBO_DAMAGE_MULTIPLIER` (x4) on
    all damage while owned.
  - **Soul box** - `SmallDemon.take_damage` now calls `target.register_kill()`
    once an enemy's hp hits 0; `Player.register_kill` adds
    `ITEM_SOUL_BOX_BONUS_PER_KILL * stacks` to a running
    `bonus_damage_from_kills`, added into every `get_damage` call from then on.
  - Sprites: `assets/graphics/white-items.png` (the first 8 items, white
    silhouettes) and `assets/graphics/red-items.png` (the 4 rarer ones),
    each rendered with an outline glow colored per `settings.ITEM_OUTLINE_COLORS`
    (white / red).
- `src/entities/DamageNumber.py` generalized from a plain damage `amount`
  to arbitrary `text` plus an optional `color` (defaults to the existing
  purple), so it could double as the "Dodged!" popup.
- Parallax background (`src/map/Background.py`'s `ParallaxBackground`,
  owned by every `Level` and rendered first each frame): a solid sky fill
  (`background.png`'s single pixel) plus four scrolling layers, back to
  front - `background-forest.png`'s wide treeline silhouette (bottom-anchored,
  barely scrolls), `huge-trees.png`'s canopy, and `tall-trees.png`'s
  bare-branch row then leafy row (both top-pinned, scaled up, scrolling
  progressively faster). Tree instances for the sheet-based layers are
  scattered at random positions/variants once per `Level`, not tiled, since
  the sheets stay wider than a level's own camera scroll range. Every
  scroll factor/height/spacing constant lives in `settings.py`
  (`BACKGROUND_*`).
- Hit VFX: `src/entities/HitEffect.py`, a one-shot 4-frame slash animation
  (`assets/graphics/blade-effects.png`'s first row) spawned centered on any
  target hit by the rage or samurai-sword AOE bursts specifically (not
  regular melee/throw hits) - `HitEffect.spawn_on(level, target)`.
- `README.md`: a first pass at the game manual/setup guide.

### Changed

- Rage rebalanced (`PLAYER_RAGE_DURATION` 2.0s → 1.0s, `PLAYER_RAGE_HITS`
  8 → 4, same 0.25s hit interval either way) to compensate for the samurai
  sword's ability to proc off rage's own hits.
- `Player.attack_hitbox_rect`/melee hitbox now dips
  `PLAYER_ATTACK_INSET` back inside Marze's own hurtbox instead of sitting
  completely flush against it, reining in how far forward the swing's
  hitbox reaches.
- `ThrownSword`'s damage is now computed once via `Player.get_damage` at
  throw time (so it benefits from the knife/soul box/crit/Jimbo bonuses)
  instead of always dealing the flat `PLAYER_THROW_DAMAGE`; its landed
  explosion (`SWORD_EXPLOSION_DAMAGE`) now routes through `get_damage` too.
- `assets/graphics/items.png` (the original flat-color 5-icon sheet) removed,
  replaced by `white-items.png`/`red-items.png` above.

### Fixed

- `PlayState`'s player spawn no longer hardcodes tile row 16 as the ground
  surface - it now looks up the actual ground row via `Level.ground_row`
  (the same way item/demon spawns already did), so editing the map's
  ground height no longer leaves the player spawning below/inside it.

## [0.1.0] - 2026-09-13

First playable build: a controllable Marze with jump/dash/melee, one
enemy type (the small demon) that spawns, chases, fights back, and dies,
and a HUD tying it all together. Still missing most of the systems
described in `CLAUDE.md` (items, difficulty tiers, the beacon/guardian
loop, real title/pause/victory screens) - this is the foundation those
build on next, not a feature-complete release.

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
- Run animation: `Marze.png` gained a second row (3 frames); `PlayingState`
  now switches between `idle`/`run` based on `move_direction` instead of
  always playing `idle`.
- Dash ability (`E` / HUD slot 3, `src/entities/player_states/DashState.py`):
  a short, gravity-cancelling horizontal burst (`PLAYER_DASH_SPEED`,
  `PLAYER_DASH_DURATION`) on `PLAYER_DASH_COOLDOWN` (3s), with its own
  5-frame animation. Also grants `PLAYER_INVINCIBILITY_DURATION` (1s) of
  invincibility - `Player.take_damage` no-ops entirely while it's active,
  and `src/ui/HUD.py`'s HP bar swaps to a solid white "INVINCIBLE" bar for
  that window instead of the normal fill/`hp/max` text.
- Front-facing melee attack (`Q` / HUD slot 1,
  `src/entities/player_states/AttackState.py`): plays a dedicated 3-frame
  swing animation, deals `PLAYER_ATTACK_DAMAGE` to anything with a
  `take_damage` method inside `Player.attack_hitbox_rect()`
  (`HIT_DELAY`-timed, not instant on enter). Rooted (`vx = 0`) while
  grounded, but keeps full movement control mid-air so a jump-attack
  doesn't stall dead in the air. `Marze.png` grew to 250x160 (50x40
  padded cells, room for the swing to animate) - `Player.sprite_offset`
  re-centers the art on the unchanged 32x32 hitbox.
- Ability HUD: `Q`/`W`/`E`/`R` map 1:1 to the 4 `marze-abilities.png`
  icons/HUD slots (`W`/`R` reserved for future abilities, currently
  unbound). Each slot reads `Player.get_ability_cooldown(slot)` and, while
  on cooldown, draws a translucent gray overlay plus the ceiling of the
  seconds remaining.
- `SmallDemon` now has `hp`/`max_hp` (`settings.DEMON_MAX_HP`) and
  `take_damage()`, which spawns a `DamageNumber` and interrupts whatever
  it was doing to play a new `HurtState` (brief stagger, then resumes
  chasing) or, once hp runs out, `DeadState` (plays the death animation
  once, then sets `is_dead` so `Level.update` drops it). `Player`'s attack
  and the demon's own attack both route incoming damage through
  `take_damage` now rather than mutating `hp` directly, so invincibility
  and hurt/death reactions apply uniformly.
- Overhead enemy health bar (`src/ui/health_bar.py`): a small red bar
  above any entity flagged `SHOW_HEALTH_BAR = True`, drawn only while
  `hp < max_hp`.
- Demon spawn animation (`SpawnState`, `small-demon.png`'s new 7th row,
  4 frames): every demon plays this once on creation before handing off
  to `FollowState`/`IdleState`.
- Periodic randomized enemy spawning: `PlayState._spawn_demon` now fires
  every `DEMON_SPAWN_INTERVAL` seconds (instead of once at level start),
  placing a demon on solid ground somewhere between
  `DEMON_SPAWN_MIN_DISTANCE_TILES` and `DEMON_SPAWN_MAX_DISTANCE_TILES`
  tiles from the player's *current* position, randomly to either side, as
  long as fewer than `DEMON_MAX_ACTIVE` are already alive.
- Debug hitbox/hurtbox overlay is now a live toggle: `H`
  (`toggle_debug_hitboxes`) flips `settings.DEBUG_HITBOXES` at runtime
  from `src.Game.on_input`, defaulting to off at startup instead of the
  overlay being permanently on.

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
- Jump is now fixed-height: removed the hold-to-jump-higher mechanic
  entirely (`jump_held`, `STOP_JUMP`, `settings.JUMP_CUT_VELOCITY` are all
  gone) and lowered `JUMP_TAKEOFF_SPEED` (`GRAVITY / 3` → `GRAVITY / 4`)
  for a smaller jump now that it's always full height.
- Ability inputs are dropped, not buffered: pressing dash/attack/jump
  while `AttackState`/`DashState` is active used to sit in
  `dash_requested`/`attack_requested`/`jump_requested` and fire the
  instant control returned to `PlayingState`. Both states now clear all
  three every frame while they're active, so a press mid-action is
  simply ignored - it has to be pressed again once the player is
  actually free to act on it.
- Attack hitboxes (`Player.attack_hitbox_rect`,
  `SmallDemon.melee_range_rect`) no longer include the attacker's own
  hurtbox width - previously `RANGE + width` starting at the attacker's
  own edge, which visibly overlapped the attacker; now just a
  `RANGE`-wide strip flush against the facing side.

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
- `DungeonProb.init()` (`src/Game.py`) registered itself as an
  `InputHandler` listener a second time on top of the registration
  `gale.game.Game.__init__` already does, so every input notified
  `on_input` twice. Harmless for one-shot commands, but it silently
  canceled out the (later added) debug-hitbox toggle - flip, then flip
  back in the same frame. Removed the redundant registration.
- Run animation pointed at stale frame indices (`[4, 5, 6]`, then
  `[7, 8, 9]`) after `Marze.png`'s column count changed with each
  subsequent sprite addition (dash row, then attack row) - `generate_frames`
  numbers frames row-major by the *current* column count, so adding
  columns shifts every later row's indices. Now `[5, 6, 7]`, matching the
  current 5-column sheet.
