# Pause Menu, Save & Load Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Esc's current "quit the app instantly" behavior with a toggleable pause menu (Resume/Save/Load/Quit), usable from any screen, backed by a full-fidelity single-slot save/load of the current run.

**Architecture:** `Game` (`src/Game.py`) gains a `gale.state.StateStack` (`pause_stack`) and a `gale.save.SaveManager`. Esc is intercepted at the `Game.on_input` level, before the existing `StateMachine` (title/play/game_over/victory) ever sees it, toggling `PauseMenuState` on/off the stack. While the stack is non-empty, `Game.update` skips the `StateMachine` entirely (freezing whichever screen is underneath) and `Game.render` draws the `StateMachine`'s frozen frame first, then the menu on top. `PlayState` gains `get_save_data()`/a `save_data=` `enter()` path that serializes/reconstructs the player, every `SmallDemon`, every `Chest`, every dropped `Pickup`, and the altar's phase — everything else (VFX, in-flight projectiles, cosmetic pillars) is dropped and regenerated or simply omitted.

**Tech Stack:** `gale.state.StateStack`, `gale.save.SaveManager`, existing project conventions (pygame, `gale.text.render_text`, the project's `src/states/*State.py` duck-typed state pattern).

**Spec:** `docs/superpowers/specs/2026-09-18-pause-menu-save-load-design.md`

## Global Constraints

- Single save slot: `settings.SAVE_SLOT = "save1"`.
- Menu reachable from every top-level screen (title/play/game_over/victory), not just during a run.
- Quit (menu option) = `self.game.quit()`, same as Esc's old global behavior.
- Save disabled (dimmed, shows "Nothing to save" if attempted) unless the current top-level state is `PlayState`.
- Load disabled (dimmed, shows "No save found" if attempted) unless a save exists; shows "Save file is corrupted" if the file exists but fails to load (`gale.save.SaveError`).
- This project has **no pytest suite** — every feature in this codebase so far has been verified with small headless smoke scripts (`SDL_AUDIODRIVER=dummy`, a hidden `pygame.display.set_mode`, plain `assert`). Follow that same convention for every task's verification step below; do not introduce pytest.
- `src/states/PauseState.py` and its `'pause'` registration in `src/Game.py` are dead code (nothing has ever transitioned to it) — delete both as part of this work.

---

### Task 1: Settings, and delete the dead PauseState

**Files:**
- Modify: `settings.py` (add `SAVE_SLOT` near the other top-level constants, e.g. right after `TITLE = "Dungeon Prob"`)
- Delete: `src/states/PauseState.py`

**Interfaces:**
- Produces: `settings.SAVE_SLOT` (`str`, value `"save1"`) — used by `PauseMenuState` (Task 7) and any save/load smoke test.

- [ ] **Step 1: Add the setting**

In `settings.py`, right after the `TITLE = "Dungeon Prob"` line, add:

```python
# gale.save.SaveManager's single slot name (src.states.PauseMenuState) -
# this game only ever has one save at a time, no slot-picker UI.
SAVE_SLOT = "save1"
```

- [ ] **Step 2: Delete the dead state file**

```bash
rm src/states/PauseState.py
```

- [ ] **Step 3: Verify nothing else references it**

Run: `grep -rn "PauseState\|'pause'" src/ settings.py`
Expected: no output (the only references were `src/Game.py`'s import/registration, which Task 8 removes — until then this grep will still show those two lines in `src/Game.py`; that's fine, confirm no *other* file references it).

- [ ] **Step 4: Commit**

```bash
git add settings.py src/states/PauseState.py
git commit -m "Add SAVE_SLOT setting, delete dead PauseState stub"
```

---

### Task 2: Player save/load

**Files:**
- Modify: `src/entities/Player.py`

**Interfaces:**
- Consumes: nothing new — reads existing `self.hp`, `self.max_hp`, `self.xp`, `self.xp_to_next_level`, `self.level_num`, `self.gold`, `self.item_stacks` (a `collections.Counter`, already imported at the top of this file), `self.bonus_damage_from_kills`, `self.bonus_damage_from_level`, `self.kills_count`, `self.total_damage_dealt`, `self.flipped`.
- Produces: `Player.to_save_dict(self) -> Dict[str, Any]`, `Player.apply_save_dict(self, data: Dict[str, Any]) -> None` — both consumed by `PlayState` in Task 6.

- [ ] **Step 1: Add the two methods**

Add these as new methods on `Player`, right after `grant_xp` (the last method before `attack_duration`'s property — search for `def grant_xp` to find the spot, add the two new methods immediately after that method's body ends):

```python
    def to_save_dict(self) -> Dict[str, Any]:
        """Everything src.states.PlayState.get_save_data needs to
        reconstruct this player on load - see apply_save_dict.
        """
        return {
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "level_num": self.level_num,
            "gold": self.gold,
            "item_stacks": dict(self.item_stacks),
            "bonus_damage_from_kills": self.bonus_damage_from_kills,
            "bonus_damage_from_level": self.bonus_damage_from_level,
            "kills_count": self.kills_count,
            "total_damage_dealt": self.total_damage_dealt,
            "flipped": self.flipped,
        }

    def apply_save_dict(self, data: Dict[str, Any]) -> None:
        """Overlays a to_save_dict() snapshot onto an already-constructed
        Player (see PlayState._load_from_save_data) - called right after
        the normal constructor, so every other field (animations,
        command bindings, cooldowns) is already set up fresh/neutral.
        """
        self.hp = data["hp"]
        self.max_hp = data["max_hp"]
        self.xp = data["xp"]
        self.xp_to_next_level = data["xp_to_next_level"]
        self.level_num = data["level_num"]
        self.gold = data["gold"]
        self.item_stacks = Counter(data["item_stacks"])
        self.bonus_damage_from_kills = data["bonus_damage_from_kills"]
        self.bonus_damage_from_level = data["bonus_damage_from_level"]
        self.kills_count = data["kills_count"]
        self.total_damage_dealt = data["total_damage_dealt"]
        self.flipped = data["flipped"]
```

`Dict`/`Any` are already imported at the top of `src/entities/Player.py` (`from typing import Optional, Tuple, TypeVar` — check this line; if `Dict`/`Any` are missing from it, add them: `from typing import Any, Dict, Optional, Tuple, TypeVar`).

- [ ] **Step 2: Verify the import line**

Run: `grep -n "^from typing import" src/entities/Player.py`
Expected: the line includes both `Any` and `Dict`. If not, edit it to include them (see Step 1's note).

- [ ] **Step 3: Write and run a round-trip smoke script**

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
from src.map.Level import Level
from src.entities.Player import Player
import settings

level = Level(settings.TILEMAPS['forest'])
player = Player(10, 20, level)
player.hp = 42
player.gold = 99
player.item_stacks['cane'] = 3
player.kills_count = 7
player.total_damage_dealt = 123.0

data = player.to_save_dict()
assert data['hp'] == 42
assert data['gold'] == 99
assert data['item_stacks'] == {'cane': 3}
assert data['kills_count'] == 7

fresh = Player(0, 0, level)
fresh.apply_save_dict(data)
assert fresh.hp == 42
assert fresh.gold == 99
assert fresh.item_stacks['cane'] == 3
assert fresh.kills_count == 7
assert fresh.total_damage_dealt == 123.0
print('Player save/load round-trip OK')
"
```

Expected output: `Player save/load round-trip OK`, no traceback.

- [ ] **Step 4: Commit**

```bash
git add src/entities/Player.py
git commit -m "Add Player.to_save_dict/apply_save_dict"
```

---

### Task 3: SmallDemon save/load

**Files:**
- Modify: `src/entities/SmallDemon.py`

**Interfaces:**
- Produces: `SmallDemon.to_save_dict(self) -> Dict[str, Any]`, `SmallDemon.apply_save_dict(self, data: Dict[str, Any]) -> None` — consumed by `PlayState` in Task 6.

- [ ] **Step 1: Add the two methods**

Add right after `__init__` (before `def take_damage`):

```python
    def to_save_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack_damage": self.attack_damage,
        }

    def apply_save_dict(self, data: Dict[str, Any]) -> None:
        """Overlays a to_save_dict() snapshot onto an already-constructed
        SmallDemon (see PlayState._load_from_save_data) - the caller is
        also responsible for calling self.change_state("follow")
        afterward, skipping the spawn animation a freshly-constructed
        demon would otherwise start in.
        """
        self.hp = data["hp"]
        self.max_hp = data["max_hp"]
        self.attack_damage = data["attack_damage"]
```

Check the top of `src/entities/SmallDemon.py` for its typing import line (`from typing import Any, Optional, TypeVar`) — `Any` is already there; add `Dict` to it: `from typing import Any, Dict, Optional, TypeVar`.

- [ ] **Step 2: Verify the import line**

Run: `grep -n "^from typing import" src/entities/SmallDemon.py`
Expected: includes `Dict`.

- [ ] **Step 3: Write and run a round-trip smoke script**

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
from src.map.Level import Level
from src.entities.Player import Player
from src.entities.SmallDemon import SmallDemon
import settings

level = Level(settings.TILEMAPS['forest'])
player = Player(0, 0, level)
demon = SmallDemon(50, 60, level, target=player, hp_multiplier=1.5, damage_multiplier=1.2)
demon.hp = 5

data = demon.to_save_dict()
assert data['hp'] == 5
assert data['max_hp'] == demon.max_hp
assert data['attack_damage'] == demon.attack_damage

fresh = SmallDemon(0, 0, level, target=player)
fresh.apply_save_dict(data)
fresh.change_state('follow')
assert fresh.hp == 5
assert fresh.max_hp == demon.max_hp
assert type(fresh.state_machine.current).__name__ == 'FollowState'
print('SmallDemon save/load round-trip OK')
"
```

Expected output: `SmallDemon save/load round-trip OK`.

- [ ] **Step 4: Commit**

```bash
git add src/entities/SmallDemon.py
git commit -m "Add SmallDemon.to_save_dict/apply_save_dict"
```

---

### Task 4: Chest save/load

**Files:**
- Modify: `src/entities/Chest.py`

**Interfaces:**
- Produces: `Chest.to_save_dict(self) -> Dict[str, Any]`, `Chest.apply_save_dict(self, data: Dict[str, Any]) -> None` — consumed by `PlayState` in Task 6.

- [ ] **Step 1: Add the two methods**

Add right after `__init__` (before `def get_collision_rect`):

```python
    def to_save_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "cost": self.cost,
            "opening": self.opening,
            "opened": self.opened,
            "frame_index": self.frame_index,
            "pending_item_id": self._pending_item_id,
            "item_spawned": self._item_spawned,
        }

    def apply_save_dict(self, data: Dict[str, Any]) -> None:
        """Overlays a to_save_dict() snapshot onto an already-constructed
        Chest (see PlayState._load_from_save_data) - self.cost, in
        particular, is randomly re-rolled by the constructor and always
        needs overwriting.
        """
        self.cost = data["cost"]
        self.opening = data["opening"]
        self.opened = data["opened"]
        self.frame_index = data["frame_index"]
        self._pending_item_id = data["pending_item_id"]
        self._item_spawned = data["item_spawned"]
```

Check `src/entities/Chest.py`'s typing import (`from typing import Any, TypeVar`) — add `Dict`: `from typing import Any, Dict, TypeVar`.

- [ ] **Step 2: Verify the import line**

Run: `grep -n "^from typing import" src/entities/Chest.py`
Expected: includes `Dict`.

- [ ] **Step 3: Write and run a round-trip smoke script**

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
from src.map.Level import Level
from src.entities.Player import Player
from src.entities.Chest import Chest
import settings

level = Level(settings.TILEMAPS['forest'])
player = Player(0, 0, level)
chest = Chest(30, 40, player, level)
chest.opening = True
chest.frame_index = 2
chest._pending_item_id = 'heart'

data = chest.to_save_dict()
assert data['opening'] is True
assert data['pending_item_id'] == 'heart'

fresh = Chest(0, 0, player, level)
fresh.apply_save_dict(data)
assert fresh.opening is True
assert fresh.frame_index == 2
assert fresh._pending_item_id == 'heart'
assert fresh.cost == chest.cost
print('Chest save/load round-trip OK')
"
```

Expected output: `Chest save/load round-trip OK`.

- [ ] **Step 4: Commit**

```bash
git add src/entities/Chest.py
git commit -m "Add Chest.to_save_dict/apply_save_dict"
```

---

### Task 5: Pickup save data

**Files:**
- Modify: `src/items/Pickup.py`

**Interfaces:**
- Produces: `Pickup.to_save_dict(self) -> Dict[str, Any]` — consumed by `PlayState` in Task 6. No `apply_save_dict` needed: on load, `PlayState` reconstructs a `Pickup` directly via its constructor, passing the saved `base_y` as the constructor's `y` argument (which sets both `self.y` and `self.base_y` to it — the float-bob phase simply resets to the anchor, a cosmetic detail nobody will notice on a paused/reloaded item).

- [ ] **Step 1: Add the method**

Add right after `__init__` (before `def get_collision_rect`):

```python
    def to_save_dict(self) -> Dict[str, Any]:
        return {"x": self.x, "base_y": self.base_y, "item_id": self.item_id}
```

Check `src/items/Pickup.py`'s typing import (`from typing import Any, TypeVar`) — add `Dict`: `from typing import Any, Dict, TypeVar`.

- [ ] **Step 2: Verify the import line**

Run: `grep -n "^from typing import" src/items/Pickup.py`
Expected: includes `Dict`.

- [ ] **Step 3: Write and run a smoke script**

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
from src.map.Level import Level
from src.entities.Player import Player
from src.items.Pickup import Pickup
import settings

level = Level(settings.TILEMAPS['forest'])
player = Player(0, 0, level)
pickup = Pickup(70, 80, 'knife', player, level)

data = pickup.to_save_dict()
assert data == {'x': 70, 'base_y': 80, 'item_id': 'knife'}

fresh = Pickup(data['x'], data['base_y'], data['item_id'], player, level)
assert fresh.x == 70
assert fresh.base_y == 80
assert fresh.item_id == 'knife'
print('Pickup save data OK')
"
```

Expected output: `Pickup save data OK`.

- [ ] **Step 4: Commit**

```bash
git add src/items/Pickup.py
git commit -m "Add Pickup.to_save_dict"
```

---

### Task 6: PlayState save/load orchestration

**Files:**
- Modify: `src/states/PlayState.py`

**Interfaces:**
- Consumes: `Player.to_save_dict/apply_save_dict` (Task 2), `SmallDemon.to_save_dict/apply_save_dict` (Task 3), `Chest.to_save_dict/apply_save_dict` (Task 4), `Pickup.to_save_dict` (Task 5).
- Produces: `PlayState.get_save_data(self) -> Dict[str, Any]`, and `PlayState.enter(self, *args, save_data=None, **kwargs)` — the `save_data` kwarg is what `PauseMenuState` (Task 7) passes via `state_machine.change("play", save_data=data)`.

- [ ] **Step 1: Add the `Pickup`/`Altar` imports and `Optional`/`Dict` typing**

`Altar` and `Dict`/`Optional` are already imported in `src/states/PlayState.py` (`from src.entities.Altar import Altar` and `from typing import Any, Dict, Optional, Tuple`). Add the missing `Pickup` import — insert this line alongside the other `src.entities.*`/`src.items.*` imports (after `from src.entities.SmallDemon import SmallDemon`):

```python
from src.items.Pickup import Pickup
```

- [ ] **Step 2: Change `enter`'s signature to accept `save_data`**

Find:
```python
    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        play_music("playing")

        self.level = Level(settings.TILEMAPS['forest'])

        self._spawn_player()
```

Replace with:
```python
    def enter(
        self,
        *args: Tuple[Any],
        save_data: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        play_music("playing")

        self.level = Level(settings.TILEMAPS['forest'])

        if save_data is not None:
            self._load_from_save_data(save_data)
            return

        self._spawn_player()
```

(Everything below `self._spawn_player()` in the existing method body — the rest of the original `enter` — stays exactly as-is, now only reached on the "fresh game" path.)

- [ ] **Step 3: Add `get_save_data`**

Add this new method right after `enter` (before `_spawn_player`):

```python
    def get_save_data(self) -> Dict[str, Any]:
        """Everything needed to fully reconstruct this run - see
        _load_from_save_data. Called by src.states.PauseMenuState's
        Save option.
        """
        demons = []
        chests = []
        pickups = []
        altar_pos = None

        for entity in self.level.entities:
            if isinstance(entity, SmallDemon):
                demons.append(entity.to_save_dict())
            elif isinstance(entity, Chest):
                chests.append(entity.to_save_dict())
            elif isinstance(entity, Pickup):
                pickups.append(entity.to_save_dict())
            elif isinstance(entity, Altar):
                altar_pos = [entity.x, entity.y]

        return {
            "elapsed_time": self.elapsed_time,
            "spawn_center_x": self._spawn_center_x,
            "spawn_ground_y": self._spawn_ground_y,
            "altar_phase": self.level.altar_phase,
            "altar_buff_timer": self.level.altar_buff_timer,
            "altar_pos": altar_pos,
            "player": self.player.to_save_dict(),
            "demons": demons,
            "chests": chests,
            "pickups": pickups,
        }
```

- [ ] **Step 4: Add `_load_from_save_data`**

Add this new method right after `get_save_data`:

```python
    def _load_from_save_data(self, data: Dict[str, Any]) -> None:
        """The save_data path through enter() - reconstructs the run
        get_save_data() captured, in place of the normal random-
        generation path (_spawn_player/_spawn_chests/_spawn_altar).
        """
        self._spawn_center_x = data["spawn_center_x"]
        self._spawn_ground_y = data["spawn_ground_y"]

        player_data = data["player"]
        self.player = Player(player_data["x"], player_data["y"], self.level)
        self.player.apply_save_dict(player_data)
        self.level.entities.append(self.player)
        self._spawn_pillars()

        self.camera = Camera(settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT)
        self.camera.bounds = self.level.get_rect()
        self.camera.follow(self.player, rate=settings.CAMERA_FOLLOW_RATE)
        self.camera.x, self.camera.y = self.player.x, self.player.y
        self.camera.update(0)

        self.spawn_timer = 0.0
        self.elapsed_time = data["elapsed_time"]
        self.current_tier = settings.DIFFICULTY_TIERS[0]
        for tier in settings.DIFFICULTY_TIERS:
            if tier["start_time"] <= self.elapsed_time:
                self.current_tier = tier

        self.hud = HUD(self.player)

        self.level.altar_phase = data["altar_phase"]
        self.level.altar_buff_timer = data["altar_buff_timer"]

        for demon_data in data["demons"]:
            demon = SmallDemon(
                demon_data["x"], demon_data["y"], self.level, target=self.player
            )
            demon.apply_save_dict(demon_data)
            demon.change_state("follow")
            self.level.entities.append(demon)

        for chest_data in data["chests"]:
            chest = Chest(chest_data["x"], chest_data["y"], self.player, self.level)
            chest.apply_save_dict(chest_data)
            self.level.entities.append(chest)

        for pickup_data in data["pickups"]:
            self.level.entities.append(
                Pickup(
                    pickup_data["x"],
                    pickup_data["base_y"],
                    pickup_data["item_id"],
                    self.player,
                    self.level,
                )
            )

        if data["altar_pos"] is not None:
            x, y = data["altar_pos"]
            altar = Altar(x, y, self.player, self.level)
            altar.frame_index = 0 if self.level.altar_phase == "inactive" else 3
            self.level.entities.append(altar)
```

- [ ] **Step 5: Write and run an end-to-end round-trip smoke script**

This is the integration test for the whole task — it drives a real `PlayState` through the `gale.state.StateMachine` exactly the way the game does, mutates it away from a fresh spawn, serializes it, feeds that into a *second* `PlayState` via `state_machine.change("play", save_data=...)`, and checks the reconstructed state matches.

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
import settings
from gale.state import StateMachine
from src.states.PlayState import PlayState
from src.entities.SmallDemon import SmallDemon
from src.entities.Chest import Chest

sm = StateMachine({'play': PlayState})
sm.change('play')
play = sm.current

play.player.gold = 250
play.player.hp = 33
play.elapsed_time = 123.0
demon = SmallDemon(play.player.x + 40, play.player.y, play.level, target=play.player)
demon.hp = 4
play.level.entities.append(demon)
chest = Chest(play.player.x - 40, play.player.y, play.player, play.level)
chest.opening = True
play.level.entities.append(chest)

data = play.get_save_data()
assert len(data['demons']) == 1
assert len(data['chests']) == 1
assert data['player']['gold'] == 250

sm.change('play', save_data=data)
loaded = sm.current

assert loaded.player.gold == 250
assert loaded.player.hp == 33
assert loaded.elapsed_time == 123.0
loaded_demons = [e for e in loaded.level.entities if isinstance(e, SmallDemon)]
assert len(loaded_demons) == 1
assert loaded_demons[0].hp == 4
assert type(loaded_demons[0].state_machine.current).__name__ == 'FollowState'
loaded_chests = [e for e in loaded.level.entities if isinstance(e, Chest)]
assert len(loaded_chests) == 1
assert loaded_chests[0].opening is True
print('PlayState save/load round-trip OK')
"
```

Expected output: `PlayState save/load round-trip OK`.

- [ ] **Step 6: Also verify the normal (non-save) path still works**

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
import settings
from gale.state import StateMachine
from src.states.PlayState import PlayState

sm = StateMachine({'play': PlayState})
sm.change('play')
print('fresh (non-save) PlayState.enter still works, player hp:', sm.current.player.hp)
"
```

Expected output: `fresh (non-save) PlayState.enter still works, player hp: <PLAYER_MAX_HP value>`, no traceback.

- [ ] **Step 7: Commit**

```bash
git add src/states/PlayState.py
git commit -m "Add PlayState.get_save_data/_load_from_save_data, save_data= enter() path"
```

---

### Task 7: PauseMenuState

**Files:**
- Create: `src/states/PauseMenuState.py`

**Interfaces:**
- Consumes: `settings.SAVE_SLOT` (Task 1), `PlayState.get_save_data` (Task 6), `gale.save.SaveManager`/`SaveError`, `gale.input_handler.InputData`, `gale.text.render_text`.
- Produces: `PauseMenuState(stack, game)` — a class with `enter(*args, **kwargs)`, `exit()`, `on_input(input_id, input_data)`, `update(dt)`, `render(surface)`, matching the duck-typed interface `gale.state.StateStack.push`/`pop` expect. Consumed by `src/Game.py` in Task 8.

- [ ] **Step 1: Write the file**

```python
"""
The pause menu (Resume/Save/Load/Quit), pushed onto src.Game.DungeonProb's
pause_stack (a gale.state.StateStack) when Esc is pressed, popped when
Esc is pressed again or "Resume" is chosen. Not a gale.state.StateMachine
state - StateStack.push/pop expects an already-constructed instance (with
its own enter()/exit(), called by push/pop themselves), so this is built
directly by Game rather than registered in any states dict, and takes the
stack and the owning Game instance directly in its constructor instead of
a state_machine.

Reachable from every top-level screen (title/play/game_over/victory),
per the design spec - Save is only meaningful while actually in
PlayState, Load works from anywhere (it fully replaces whatever
top-level state was showing with a freshly-loaded PlayState).
"""

from typing import Any, Dict, Tuple

import pygame

from gale.input_handler import InputData
from gale.save import SaveError
from gale.text import render_text

import settings
from src.states.PlayState import PlayState

TITLE_FONT_SIZE = 32
OPTION_FONT_SIZE = 18
MESSAGE_FONT_SIZE = 14

TITLE_Y = settings.VIRTUAL_HEIGHT // 3
OPTIONS_START_Y = TITLE_Y + 50
OPTION_SPACING = 28
MESSAGE_Y = OPTIONS_START_Y + 4 * OPTION_SPACING + 20

OVERLAY_COLOR = (0, 0, 0, 160)
TITLE_COLOR = pygame.Color(235, 235, 235)
OPTION_COLOR = pygame.Color(200, 200, 200)
SELECTED_COLOR = pygame.Color(255, 215, 90)
DISABLED_COLOR = pygame.Color(110, 110, 110)
MESSAGE_COLOR = pygame.Color(120, 220, 140)

OPTIONS = ["Resume", "Save", "Load", "Quit"]

MESSAGE_DURATION = 1.5


class PauseMenuState:
    def __init__(self, stack: Any, game: Any) -> None:
        self.stack = stack
        self.game = game

    def enter(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        self.selected = 0
        self.title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
        self.option_font = pygame.font.Font(None, OPTION_FONT_SIZE)
        self.message_font = pygame.font.Font(None, MESSAGE_FONT_SIZE)

        self.overlay = pygame.Surface(
            (settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), pygame.SRCALPHA
        )
        self.overlay.fill(OVERLAY_COLOR)

        self.message = ""
        self.message_timer = 0.0

    def exit(self) -> None:
        pass

    def _in_play(self) -> bool:
        return isinstance(self.game.state_machine.current, PlayState)

    def _option_enabled(self, option: str) -> bool:
        if option == "Save":
            return self._in_play()
        if option == "Load":
            return self.game.save_manager.exists(settings.SAVE_SLOT)
        return True

    def _show_message(self, text: str) -> None:
        self.message = text
        self.message_timer = MESSAGE_DURATION

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if not input_data.pressed:
            return

        if input_id == "move_up":
            self.selected = (self.selected - 1) % len(OPTIONS)
        elif input_id == "move_down":
            self.selected = (self.selected + 1) % len(OPTIONS)
        elif input_id == "start":
            self._activate(OPTIONS[self.selected])

    def _activate(self, option: str) -> None:
        if option == "Resume":
            self.stack.pop()
        elif option == "Save":
            if not self._in_play():
                self._show_message("Nothing to save")
                return
            data = self.game.state_machine.current.get_save_data()
            self.game.save_manager.save(settings.SAVE_SLOT, data)
            self._show_message("Saved!")
        elif option == "Load":
            if not self.game.save_manager.exists(settings.SAVE_SLOT):
                self._show_message("No save found")
                return
            try:
                data = self.game.save_manager.load(settings.SAVE_SLOT)
            except SaveError:
                self._show_message("Save file is corrupted")
                return
            self.game.state_machine.change("play", save_data=data)
            self.stack.pop()
        elif option == "Quit":
            self.game.quit()

    def update(self, dt: float) -> None:
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.overlay, (0, 0))

        render_text(
            surface,
            "Paused",
            self.title_font,
            settings.VIRTUAL_WIDTH // 2,
            TITLE_Y,
            TITLE_COLOR,
            center=True,
            shadowed=True,
        )

        for i, option in enumerate(OPTIONS):
            if not self._option_enabled(option):
                color = DISABLED_COLOR
            elif i == self.selected:
                color = SELECTED_COLOR
            else:
                color = OPTION_COLOR

            render_text(
                surface,
                option,
                self.option_font,
                settings.VIRTUAL_WIDTH // 2,
                OPTIONS_START_Y + i * OPTION_SPACING,
                color,
                center=True,
                shadowed=True,
            )

        if self.message:
            render_text(
                surface,
                self.message,
                self.message_font,
                settings.VIRTUAL_WIDTH // 2,
                MESSAGE_Y,
                MESSAGE_COLOR,
                center=True,
                shadowed=True,
            )
```

- [ ] **Step 2: Syntax check**

Run: `python3 -c "import ast; ast.parse(open('src/states/PauseMenuState.py').read()); print('syntax ok')"`
Expected: `syntax ok`.

- [ ] **Step 3: Write and run a smoke script**

This constructs a `PauseMenuState` directly (the way `Game` will in Task 8, not via any `StateMachine`), drives it through a `StateStack`, and checks navigation, Save/Load gating, and messages.

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
import settings
from gale.state import StateStack, StateMachine
from gale.save import SaveManager
from gale.input_handler import InputData
from src.states.PlayState import PlayState
from src.states.TitleState import TitleState
from src.states.PauseMenuState import PauseMenuState

class FakeGame:
    def __init__(self):
        self.state_machine = StateMachine({'title': TitleState, 'play': PlayState})
        self.state_machine.change('title')
        self.save_manager = SaveManager(save_dir='/tmp/dungeonprob_test_saves')
        self.quit_called = False
    def quit(self):
        self.quit_called = True

game = FakeGame()
stack = StateStack()
menu = PauseMenuState(stack, game)
stack.push(menu)

surf = pygame.Surface((settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT))
stack.render(surf)
print('initial render ok, selected:', menu.selected)

# navigate down to 'Save'
stack.on_input('move_down', InputData(pressed=True))
assert menu.selected == 1

# Save while on the title screen (not PlayState) -> disabled, message shown
stack.on_input('start', InputData(pressed=True))
assert menu.message == 'Nothing to save'
print('Save-disabled-outside-PlayState message OK')

# switch the underlying game to PlayState, try Save for real
game.state_machine.change('play')
stack.on_input('start', InputData(pressed=True))
assert menu.message == 'Saved!'
assert game.save_manager.exists(settings.SAVE_SLOT)
print('Save while in PlayState OK')

# navigate to Load, activate it
stack.on_input('move_up', InputData(pressed=True))
stack.on_input('start', InputData(pressed=True))
assert isinstance(game.state_machine.current, PlayState)
assert len(stack.states) == 0
print('Load closes the menu and swaps in the loaded PlayState OK')

# reopen, go to Quit
stack.push(PauseMenuState(stack, game))
stack.on_input('move_up', InputData(pressed=True))
stack.on_input('start', InputData(pressed=True))
assert game.quit_called is True
print('Quit calls game.quit() OK')

import shutil
shutil.rmtree('/tmp/dungeonprob_test_saves', ignore_errors=True)
print('all PauseMenuState checks passed')
"
```

Expected output ends with `all PauseMenuState checks passed`, no traceback.

- [ ] **Step 4: Commit**

```bash
git add src/states/PauseMenuState.py
git commit -m "Add PauseMenuState (Resume/Save/Load/Quit)"
```

---

### Task 8: Wire the pause stack into Game

**Files:**
- Modify: `src/Game.py`

**Interfaces:**
- Consumes: `PauseMenuState` (Task 7), `gale.state.StateStack`, `gale.save.SaveManager`.
- Produces: `DungeonProb.pause_stack` (a `StateStack`), `DungeonProb.save_manager` (a `SaveManager`) — both read by `PauseMenuState` via the `game` reference it was constructed with.

- [ ] **Step 1: Rewrite the file**

Replace the entire contents of `src/Game.py` with:

```python
import pygame

from gale.game import Game
from gale.input_handler import InputData, InputListener
from gale.save import SaveManager
from gale.state import StateMachine, StateStack

import settings
from src.states.TitleState import TitleState
from src.states.PlayState import PlayState
from src.states.GameOverState import GameOverState
from src.states.VictoryState import VictoryState
from src.states.PauseMenuState import PauseMenuState


class DungeonProb(Game, InputListener):
    def init(self) -> None:
        self.state_machine = StateMachine({
            'title': TitleState,
            'play': PlayState,
            'game_over': GameOverState,
            'victory': VictoryState,
        })
        self.state_machine.change('title')

        # The pause menu (src.states.PauseMenuState) - empty stack means
        # "not paused". Esc (on_input's "quit" branch below) pushes/pops
        # it; while non-empty, update() skips state_machine entirely
        # (freezing whichever screen is underneath) and render() draws
        # it on top of state_machine's own (frozen) frame.
        self.pause_stack = StateStack()
        self.save_manager = SaveManager()

    def update(self, dt: float) -> None:
        if self.pause_stack.states:
            self.pause_stack.update(dt)
            return
        self.state_machine.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.state_machine.render(surface)
        if self.pause_stack.states:
            self.pause_stack.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == 'quit' and input_data.pressed:
            if self.pause_stack.states:
                self.pause_stack.pop()
            else:
                self.pause_stack.push(PauseMenuState(self.pause_stack, self))
            return

        if self.pause_stack.states:
            self.pause_stack.on_input(input_id, input_data)
            return

        if input_id == 'toggle_debug_hitboxes' and input_data.pressed:
            settings.DEBUG_HITBOXES = not settings.DEBUG_HITBOXES
        else:
            self.state_machine.on_input(input_id, input_data)
```

- [ ] **Step 2: Syntax check**

Run: `python3 -c "import ast; ast.parse(open('src/Game.py').read()); print('syntax ok')"`
Expected: `syntax ok`.

- [ ] **Step 3: Write and run a smoke script**

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.init()
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
from gale.input_handler import InputData
from src.Game import DungeonProb
from src.states.PauseMenuState import PauseMenuState

game = DungeonProb.__new__(DungeonProb)
game.init()
assert len(game.pause_stack.states) == 0

game.on_input('quit', InputData(pressed=True))
assert len(game.pause_stack.states) == 1
assert isinstance(game.pause_stack.states[0], PauseMenuState)
print('Esc opens the pause menu OK')

state_before = type(game.state_machine.current).__name__
game.update(0.1)
assert type(game.state_machine.current).__name__ == state_before
print('state_machine frozen while paused OK')

game.on_input('quit', InputData(pressed=True))
assert len(game.pause_stack.states) == 0
print('Esc again closes the pause menu OK')
"
```

Expected output ends with `Esc again closes the pause menu OK`, no traceback.

- [ ] **Step 4: Verify the full game boots and Esc works with a real render pass**

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.init()
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
import settings
from gale.input_handler import InputData
from src.Game import DungeonProb

game = DungeonProb.__new__(DungeonProb)
game.init()
surf = pygame.Surface((settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT))

game.render(surf)
game.on_input('quit', InputData(pressed=True))
game.update(0.016)
game.render(surf)
print('paused render (title screen frozen + menu overlay) OK')

game.on_input('start', InputData(pressed=True))
game.on_input('quit', InputData(pressed=True))
game.update(0.016)
game.render(surf)
print('resumed render OK, current state:', type(game.state_machine.current).__name__)
"
```

Expected output ends with `resumed render OK, current state: TitleState`, no traceback. (The `'start'` press before closing the menu is inert here since we never navigated to "Resume" — the second `'quit'` press is what actually pops the menu; this just also exercises `on_input` routing to the menu instead of gameplay while paused.)

- [ ] **Step 5: Commit**

```bash
git add src/Game.py
git commit -m "Wire pause_stack + save_manager into Game, Esc toggles the pause menu"
```

---

### Task 9: Final end-to-end verification

**Files:** none (verification only).

- [ ] **Step 1: Full lifecycle smoke test**

Drives the real `DungeonProb` game object through: title → play → open menu → save → close menu → keep playing → die → game over → open menu → load → confirm the loaded run's stats come back.

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
SDL_AUDIODRIVER=dummy /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import pygame
pygame.init()
pygame.display.set_mode((1,1), flags=pygame.HIDDEN)
import settings
from gale.input_handler import InputData
from src.Game import DungeonProb
from src.states.PlayState import PlayState
from src.states.GameOverState import GameOverState

save_path = settings.SAVE_DIR if isinstance(settings.SAVE_DIR, str) else str(settings.SAVE_DIR)

game = DungeonProb.__new__(DungeonProb)
game.init()
game.state_machine.change('play')
game.state_machine.current.player.gold = 500
game.state_machine.current.player.hp = 10

# open menu, navigate to Save, activate
game.on_input('quit', InputData(pressed=True))
game.pause_stack.states[0].on_input('move_down', InputData(pressed=True))
game.pause_stack.states[0].on_input('start', InputData(pressed=True))
assert game.pause_stack.states[0].message == 'Saved!'
print('saved mid-run OK')

# close menu, resume
game.on_input('quit', InputData(pressed=True))
assert len(game.pause_stack.states) == 0

# kill the player -> game over
game.state_machine.current.player.hp = 0
game.update(0.016)
assert isinstance(game.state_machine.current, GameOverState)
print('died -> GameOverState OK')

# open menu from the game-over screen, navigate to Load, activate
game.on_input('quit', InputData(pressed=True))
menu = game.pause_stack.states[0]
menu.on_input('move_down', InputData(pressed=True))
menu.on_input('move_down', InputData(pressed=True))
menu.on_input('start', InputData(pressed=True))
assert isinstance(game.state_machine.current, PlayState)
assert game.state_machine.current.player.gold == 500
assert game.state_machine.current.player.hp == 10
assert len(game.pause_stack.states) == 0
print('loaded from GameOverState back into PlayState OK, stats restored')

game.save_manager.delete(settings.SAVE_SLOT)
print('ALL END-TO-END CHECKS PASSED')
"
```

Expected output ends with `ALL END-TO-END CHECKS PASSED`, no traceback.

- [ ] **Step 2: Clean up any stray save files this task's manual testing left behind**

```bash
cd /Users/brnmarq/Documents/BrnCode/DungeonProb/.claude/worktrees/title-screen
rm -rf saves/
git status --short
```

Expected: `saves/` isn't tracked by git (confirm `git status --short` shows nothing for it) — `gale.save.SaveManager`'s default `save_dir` is a relative `"saves"` directory created on first use; it's a runtime artifact, not something to commit. If `git status` shows it as untracked, that's fine (it's gitignored or simply not staged) — just don't `git add` it.

- [ ] **Step 3: Update CHANGELOG.md**

This project keeps a `CHANGELOG.md` (see its existing entries for style). Add a new entry near the top describing this feature in the same style as existing entries (past-tense, references the key files/classes). Read the last 2-3 entries first (`head -40 CHANGELOG.md`) to match formatting exactly.

- [ ] **Step 4: Final commit**

```bash
git add CHANGELOG.md
git commit -m "Update CHANGELOG for pause menu + save/load"
```

