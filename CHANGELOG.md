# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project has no releases yet, so everything lives under **Unreleased**
until the first tagged version.

## [Unreleased]

### Added

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
