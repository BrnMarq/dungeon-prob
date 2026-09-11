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

### Changed

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
