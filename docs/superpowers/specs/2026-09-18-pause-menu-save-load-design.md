# Pause Menu, Save & Load — Design

## Goal

Replace Esc's current behavior (instant `Game.quit()`) with a toggleable
pause menu, usable from any screen, offering Resume, Save, Load, and
Quit. Save/Load persist a full run snapshot (player, demons, chests,
altar, dropped pickups) via `gale.save.SaveManager`, into a single named
slot, via `gale.state.StateStack` for the overlay.

## Architecture

`DungeonProb` (`src/Game.py`) gains:

- `self.pause_stack = StateStack()` — empty when not paused.
- `self.save_manager = SaveManager()` — one instance, default settings
  (`settings.SAVE_DIR`/`SAVE_VERSION`/`SAVE_FILE_EXTENSION`, all already
  provided by `gale.conf.global_settings`).

`on_input`: the `"quit"` (Esc) branch no longer calls `self.quit()`.
Instead:

```python
if input_id == "quit" and input_data.pressed:
    if self.pause_stack.states:
        self.pause_stack.pop()
    else:
        self.pause_stack.push(PauseMenuState(self.pause_stack, self))
    return

if self.pause_stack.states:
    self.pause_stack.on_input(input_id, input_data)
    return

# ...existing toggle_debug_hitboxes / state_machine.on_input dispatch
```

`update`: if `self.pause_stack.states`, update only the stack (freezing
`self.state_machine` entirely); else update `self.state_machine` as
today.

`render`: always render `self.state_machine` first (so the frozen frame
still shows), then, if paused, a dim full-screen overlay rect followed
by `self.pause_stack.render(surface)`.

This intercepts Esc before it ever reaches `state_machine`, so it works
uniformly on the title, play, game-over, and victory screens alike, and
requires no changes to any of those states' own `on_input`.

`src/states/PauseState.py` (currently a dead forwarding stub — the
`'pause'` state_machine entry has never been reachable since nothing
transitions to it) is deleted, along with its registration in
`DungeonProb.init`'s `states` dict.

## PauseMenuState

New file `src/states/PauseMenuState.py`. Not a `StateMachine` state (no
`state_machine` constructor arg) — constructed directly by `Game` as
`PauseMenuState(stack, game)` and pushed onto `pause_stack`, per
`StateStack`'s own contract (`push(state, *args, **kwargs)` calls
`state.enter(*args, **kwargs)` immediately after appending, `pop()`
calls `state.exit()`). Implements the same duck-typed interface as
every other state (`enter`, `exit`, `on_input`, `update`, `render`), but
`stack`/`game` are stored from the constructor instead of `enter`'s
args.

Renders a centered panel (same `render_text`/font-size conventions as
`TitleState`/`GameOverState`/`VictoryState`) with four options in fixed
order: **Resume**, **Save**, **Load**, **Quit**. `move_up`/`move_down`
change the highlighted option (wrapping); `start` (Enter) activates it.

- **Resume**: `self.stack.pop()`.
- **Save**: enabled only when `isinstance(self.game.state_machine.current, PlayState)`
  — shown dimmed/unselectable otherwise (selecting it while dimmed is a
  no-op). When enabled and activated: calls the current `PlayState`'s
  `get_save_data()`, writes it via
  `self.game.save_manager.save(settings.SAVE_SLOT, data)`, and shows an
  inline "Saved!" message for `SAVE_MESSAGE_DURATION` seconds.
- **Load**: enabled only if `self.game.save_manager.exists(settings.SAVE_SLOT)`.
  When activated: reads the slot via `save_manager.load(...)`, calls
  `self.game.state_machine.change("play", save_data=data)`, then pops
  itself off the stack. Works from any screen — including mid-run,
  where it discards the current run in favor of the loaded one, same as
  today's `state_machine.change` semantics elsewhere (no confirmation
  prompt; simple is fine given a single slot). If no save exists,
  attempting Load shows an inline "No save found" message instead.
- **Quit**: `self.game.quit()`.

`settings.SAVE_SLOT = "save1"` (a single constant, since this is a
single-slot design — no slot-picker UI).

## Save data schema

`PlayState` gains two methods:

- `get_save_data(self) -> dict`: builds the full snapshot below.
- `enter(self, *args, save_data=None, **kwargs)`: when `save_data` is
  given, skips the normal random generation path (`_spawn_player`,
  `_spawn_chests`, `_spawn_altar`, `_spawn_pillars`) entirely and
  instead calls a new `self._load_from_save_data(save_data)`.

Top-level shape:

```python
{
    "elapsed_time": float,
    "spawn_center_x": float,       # for pillar placement on load
    "spawn_ground_y": float,
    "altar_phase": str,
    "altar_buff_timer": float,
    "player": {...},               # see below
    "demons": [{...}, ...],
    "chests": [{...}, ...],
    "pickups": [{...}, ...],
    "altar_pos": [x, y],
}
```

**Player** (`Player.to_save_dict()` / `Player.apply_save_dict(data)`,
new methods on `src/entities/Player.py`):

```python
{
    "x": float, "y": float,
    "hp": int, "max_hp": int,
    "xp": int, "xp_to_next_level": int,
    "level_num": int,
    "gold": int,
    "item_stacks": {item_id: count, ...},   # dict(Counter) - JSON-safe
    "bonus_damage_from_kills": float,
    "bonus_damage_from_level": float,
    "kills_count": int,
    "total_damage_dealt": float,
    "flipped": bool,
}
```

`apply_save_dict` is called right after a normal `Player(...)`
construction (so all the usual setup — animations, command bindings —
still runs), overwriting just these fields. Cooldown timers,
invincibility, and current player-state are left at their fresh-`Player`
defaults (neutral "playing" state) rather than persisted — reasonable
since Save only happens while paused, never mid-swing.

**SmallDemon** (`SmallDemon.to_save_dict()` / reconstruction helper in
`src/entities/SmallDemon.py`):

```python
{"x": float, "y": float, "hp": int, "max_hp": int, "attack_damage": int}
```

Reconstructed via the normal constructor (`hp_multiplier`/
`damage_multiplier` both `1.0`, since we overwrite the derived fields
directly afterward), then `demon.hp = ...`, `demon.max_hp = ...`,
`demon.attack_damage = ...`, and `demon.change_state("follow")`
immediately (skipping the spawn animation — it already exists, it
didn't just spawn).

**Chest** (`Chest.to_save_dict()` / reconstruction helper):

```python
{
    "x": float, "y": float, "cost": int,
    "opening": bool, "opened": bool, "frame_index": int,
    "pending_item_id": Optional[str], "item_spawned": bool,
}
```

Reconstructed via the normal constructor (which rolls a fresh `cost` —
immediately overwritten) then all the above fields restored directly,
including the private `_pending_item_id`/`_item_spawned`.

**Pickup** (dropped, not-yet-collected items only — e.g. a chest's
revealed-but-not-collected reward; new `Pickup.to_save_dict()`):

```python
{"x": float, "y": float, "base_y": float, "item_id": str}
```

**Altar**: only `altar_pos: [x, y]` at the top level — its actual
lifecycle (`phase`, `buff_timer`) is `Level` state, saved once as
`altar_phase`/`altar_buff_timer` rather than per-entity. On load, the
reconstructed `Altar`'s `frame_index` is snapped directly to match the
phase (dormant frame `0` for `"inactive"`, the final activate frame for
everything else) rather than replaying the activation animation.

**Not saved** (dropped on save, absent after load — all short-lived
VFX/projectiles, harmless to lose since Save only happens while
paused): `DamageNumber`, `HitEffect`, `ShadowExplosion`, `ItemPopup`,
any in-flight `ThrownSword`. The cosmetic spawn-flanking `Decoration`
pillars aren't saved either — `_spawn_pillars()` is deterministic given
`spawn_center_x`/`spawn_ground_y`, so it's simply called again on load.

**Difficulty tier** is never stored — it's already deterministically
derived from `elapsed_time` every frame in `PlayState.update` (looping
`settings.DIFFICULTY_TIERS`), so restoring `elapsed_time` alone is
sufficient. `spawn_timer` (the demon-spawn countdown) is reset to the
resumed tier's `spawn_interval` on load rather than persisted — a minor,
inconsequential liberty.

## Error handling

- `SaveManager.load`/`.exists` raising `SaveError` (corrupted file):
  treated the same as "no save found" for `Load`'s enabled/disabled
  check and shows the same inline message; never crashes the menu.
- Saving itself (`SaveManager.save`) is atomic (temp file + rename,
  already handled inside `gale.save`) — no extra error handling needed
  on our side beyond letting any unexpected exception propagate (would
  indicate a real bug, e.g. a non-JSON-serializable value slipping into
  the dict — guarded against by construction, since every field above is
  a plain `int`/`float`/`str`/`bool`/`dict`/`list`).

## Testing

Since this is headless-testable (as every prior feature in this session
has been, via `SDL_AUDIODRIVER=dummy` + a hidden display surface):

- Round-trip test: build a `PlayState`, mutate player/demon/chest state
  away from defaults, `get_save_data()`, construct a fresh `PlayState`
  with `save_data=...`, assert the reconstructed state matches.
- `Game`-level test: verify `pause_stack` toggles open/closed on
  repeated `"quit"` inputs, and that `state_machine.update` is skipped
  while it's open.
- Menu enabled/disabled test: `Save` disabled outside `PlayState`,
  `Load` disabled with no save file present.
