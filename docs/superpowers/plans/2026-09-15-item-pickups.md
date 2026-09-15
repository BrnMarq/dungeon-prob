# Item Pickups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add five stackable stat-boosting item pickups (`assets/graphics/items.png`), applied through new `Player` derived-stat properties, spawned at the end of the forest map for manual testing.

**Architecture:** A small `src/items/` registry (`definitions.py`) maps item ids to sprite frames. A duck-typed `Pickup` entity (same shape as `ThrownSword`/`DamageNumber`) applies its item's effect to the player on touch via `Player.collect_item`. `Player` tracks per-item stack counts in a `Counter` and exposes the *effective* values (`speed`, `get_damage()`, `attack_duration`, resistance inside `take_damage`) that every ability state already reads — states are updated to read those instead of the raw `settings` constants they use today.

**Tech Stack:** Python 3.14, pygame 2.6, gale-engine. No test framework in this repo — verification is headless smoke scripts run with `SDL_VIDEODRIVER=dummy` (established pattern from this session's R-ability work), not committed to the repo.

**Spec:** `docs/superpowers/specs/2026-09-15-item-pickups-design.md`

## Global Constraints

- Per-stack magnitudes (from the spec, "conservative" tier): cane +10% move speed (additive per stack), heart +20 max HP (also heals on pickup), knife +10% damage multiplier (additive per stack), shield ×0.92 damage taken (compounding per stack, diminishing returns), daggers ×0.9 attack duration (compounding per stack), floored at 0.05s.
- Dash speed (`settings.PLAYER_DASH_SPEED`) is NOT affected by the cane — it's a fixed burst, not "movement speed."
- The attack animation's frame *interval* (set once in `Player.__init__` from `settings.PLAYER_ATTACK_DURATION`) does not retime when attack speed changes — only the state's own elapsed-time-vs-duration check does. This is a known, accepted visual wrinkle (see spec's Non-goals).
- No HUD/inventory display, no pickup VFX/SFX, no drop tables/rarity/random spawns — fixed test spawn of one of each item only.
- White outline is already baked into `items.png`'s art — no outline rendering code.

---

### Task 1: Register items.png and per-stack constants in settings.py

**Files:**
- Modify: `settings.py`

**Interfaces:**
- Produces: `settings.TEXTURES["items"]`, `settings.FRAMES["items"]` (16×16 cells), and constants `ITEM_SPEED_BONUS`, `ITEM_HP_BONUS`, `ITEM_DAMAGE_BONUS`, `ITEM_RESISTANCE_FACTOR`, `ITEM_ATTACK_SPEED_FACTOR`, `ITEM_ATTACK_DURATION_FLOOR` — all consumed by Task 3.

- [ ] **Step 1: Add the texture/frame registration**

In `settings.py`, inside the `TEXTURES = { ... }` dict, add (after the `dark_sword` entry):

```python
    # 80x16 - 5 distinct 16x16 item icons (stat-boosting pickups,
    # src.items.Pickup), each with a white outline baked into the art.
    # Frame indices 0-4, in src.items.definitions.ITEMS order: cane,
    # heart, knife, shield, daggers.
    "items": pygame.image.load(BASE_DIR / "assets" / "graphics" / "items.png"),
```

Inside the `FRAMES = { ... }` dict, add (after the `dark_sword` entry):

```python
    "items": frames.generate_frames(TEXTURES["items"], 16, 16),
```

- [ ] **Step 2: Add the per-stack constants**

At the end of `settings.py`, after the `PLAYER_XP_TO_NEXT_LEVEL = 100` line, add:

```python
# Stat-boosting item pickups (src.items.Pickup / src.items.definitions) -
# each is stackable (src.entities.Player.item_stacks), applying its bonus
# again per pickup of the same item. Cane/knife/heart stack additively;
# shield/daggers stack multiplicatively (diminishing returns) so neither
# can reach 0 - see Player.speed/get_damage/attack_duration/take_damage.
ITEM_SPEED_BONUS = 0.10  # Walking cane - fraction of PLAYER_SPEED, per stack
ITEM_HP_BONUS = 20  # Frozen heart - flat max_hp (and immediate heal), per stack
ITEM_DAMAGE_BONUS = 0.10  # Bloody knife - fraction of base damage, per stack
ITEM_RESISTANCE_FACTOR = 0.92  # Aegis shield - incoming damage multiplier, per stack
ITEM_ATTACK_SPEED_FACTOR = 0.9  # Short daggers - attack duration multiplier, per stack
ITEM_ATTACK_DURATION_FLOOR = 0.05  # Floor so daggers stacks can't zero out the swing
```

- [ ] **Step 3: Verify it loads**

Run: `SDL_VIDEODRIVER=dummy PYTHONPATH=. /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "import settings; print(len(settings.FRAMES['items'])); print(settings.ITEM_RESISTANCE_FACTOR)"`
Expected: prints `5` then `0.92`, no traceback.

- [ ] **Step 4: Commit**

```bash
git add settings.py
git commit -m "Register items.png and item pickup stat constants"
```

---

### Task 2: Create the item definitions registry

**Files:**
- Create: `src/items/definitions.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `ITEM_CANE`, `ITEM_HEART`, `ITEM_KNIFE`, `ITEM_SHIELD`, `ITEM_DAGGERS` (str constants) and `ITEMS: Dict[str, Dict[str, int]]` mapping each id to `{"frame_index": int}` — consumed by `Player` (Task 3, for the stack-count keys) and `Pickup` (Task 6, for `frame_index`).

- [ ] **Step 1: Write the registry**

```python
"""
Effects registry for stat-boosting item pickups (src.items.Pickup). Each
entry only needs a sprite frame index - the *effect* of picking one up
is resolved by src.entities.Player.collect_item keying on the item id,
since each effect touches a different Player stat in a different way
(additive vs. compounding) and forcing that into a generic shape here
would be more machinery than five items justifies. Generalize this once
a sixth item needs a genuinely uniform "modify stat X by Y" shape.
"""

from typing import Dict

ITEM_CANE = "cane"
ITEM_HEART = "heart"
ITEM_KNIFE = "knife"
ITEM_SHIELD = "shield"
ITEM_DAGGERS = "daggers"

# assets/graphics/items.png - 80x16, five 16x16 icons, row-major.
ITEMS: Dict[str, Dict[str, int]] = {
    ITEM_CANE: {"frame_index": 0},
    ITEM_HEART: {"frame_index": 1},
    ITEM_KNIFE: {"frame_index": 2},
    ITEM_SHIELD: {"frame_index": 3},
    ITEM_DAGGERS: {"frame_index": 4},
}
```

- [ ] **Step 2: Verify it imports**

Run: `PYTHONPATH=. /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "from src.items.definitions import ITEMS, ITEM_CANE; print(ITEMS[ITEM_CANE])"`
Expected: `{'frame_index': 0}`

- [ ] **Step 3: Commit**

```bash
git add src/items/definitions.py
git commit -m "Add item pickup effects registry"
```

---

### Task 3: Add stacking + derived stats to Player

**Files:**
- Modify: `src/entities/Player.py`

**Interfaces:**
- Consumes: `settings.ITEM_*` constants (Task 1), `src.items.definitions.ITEM_CANE/ITEM_HEART/ITEM_KNIFE/ITEM_SHIELD/ITEM_DAGGERS` (Task 2).
- Produces: `player.item_stacks: Counter[str]`, `player.collect_item(item_id: str) -> None`, `player.speed` (property, float), `player.get_damage(base: float) -> int`, `player.attack_duration` (property, float), and a resistance-applying `player.take_damage` — all consumed by Task 4 (ability states), Task 6 (`Pickup.update` calls `collect_item`).

- [ ] **Step 1: Add the imports**

In `src/entities/Player.py`, replace:

```python
from typing import Optional, Tuple, TypeVar

import pygame
```

with:

```python
from collections import Counter
from typing import Optional, Tuple, TypeVar

import pygame
```

Then replace:

```python
from src.entities.player_states import (
    AttackState,
    DashState,
    PlayingState,
    RageState,
    ThrowState,
)
```

with:

```python
from src.entities.player_states import (
    AttackState,
    DashState,
    PlayingState,
    RageState,
    ThrowState,
)
from src.items.definitions import (
    ITEM_CANE,
    ITEM_DAGGERS,
    ITEM_HEART,
    ITEM_KNIFE,
    ITEM_SHIELD,
)
```

- [ ] **Step 2: Track stacks in `__init__`**

Immediately after the existing `self.invincible_timer = 0.0` line, add:

```python
        self.item_stacks: Counter = Counter()
```

- [ ] **Step 3: Add `collect_item` and the derived-stat accessors**

Add these methods to `Player`, right after the `is_invincible` property (before `take_damage`):

```python
    def collect_item(self, item_id: str) -> None:
        """Called by src.items.Pickup.update on touch - bumps the stack
        count and, for the heart only, applies its effect immediately
        (max_hp/hp are plain fields, not derived, so there's nothing to
        recompute on demand the way speed/get_damage/attack_duration
        below are). The other four items have no state beyond the stack
        count itself.
        """
        self.item_stacks[item_id] += 1
        if item_id == ITEM_HEART:
            self.max_hp += settings.ITEM_HP_BONUS
            self.hp += settings.ITEM_HP_BONUS

    @property
    def speed(self) -> float:
        """Effective move speed - settings.PLAYER_SPEED plus the walking
        cane's stacks, read by every state's movement instead of the raw
        setting. Dash stays on settings.PLAYER_DASH_SPEED, unaffected -
        it's a fixed burst, not "movement speed."
        """
        return settings.PLAYER_SPEED * (
            1 + settings.ITEM_SPEED_BONUS * self.item_stacks[ITEM_CANE]
        )

    def get_damage(self, base: float) -> int:
        """base scaled by the bloody knife's stacks - called by
        AttackState/RageState with their own damage constant, and by
        ThrowState when spawning a ThrownSword.
        """
        return round(
            base * (1 + settings.ITEM_DAMAGE_BONUS * self.item_stacks[ITEM_KNIFE])
        )

    @property
    def attack_duration(self) -> float:
        """settings.PLAYER_ATTACK_DURATION shortened by the short
        daggers' stacks (compounding, floored so it can never hit 0) -
        read by AttackState instead of the raw setting. The "attack"
        animation's own frame interval does NOT retime with this -
        see the design spec's Non-goals.
        """
        return max(
            settings.ITEM_ATTACK_DURATION_FLOOR,
            settings.PLAYER_ATTACK_DURATION
            * settings.ITEM_ATTACK_SPEED_FACTOR ** self.item_stacks[ITEM_DAGGERS],
        )
```

- [ ] **Step 4: Apply resistance in `take_damage`**

Replace:

```python
        if self.is_invincible:
            return

        self.hp = max(0, self.hp - amount)
```

with:

```python
        if self.is_invincible:
            return

        amount = round(
            amount * settings.ITEM_RESISTANCE_FACTOR ** self.item_stacks[ITEM_SHIELD]
        )
        self.hp = max(0, self.hp - amount)
```

- [ ] **Step 5: Write and run a headless smoke test**

Save as `/private/tmp/claude-501/-Users-brnmarq-Documents-BrnCode-DungeonProb/82346956-d0a8-4072-8d2e-fceecf6217e7/scratchpad/smoke_player_stats.py` (scratchpad, not committed):

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
pygame.display.set_mode((1, 1))

import settings
from src.map.Level import Level
from src.entities.Player import Player
from src.items.definitions import ITEM_CANE, ITEM_DAGGERS, ITEM_HEART, ITEM_KNIFE, ITEM_SHIELD

level = Level(settings.TILEMAPS["forest"])
player = Player(16, 100, level)

assert player.speed == settings.PLAYER_SPEED
player.collect_item(ITEM_CANE)
player.collect_item(ITEM_CANE)
assert player.speed == settings.PLAYER_SPEED * 1.20, player.speed

assert player.get_damage(15) == 15
player.collect_item(ITEM_KNIFE)
player.collect_item(ITEM_KNIFE)
assert player.get_damage(15) == 18, player.get_damage(15)  # 15 * 1.20

start_max_hp = player.max_hp
start_hp = player.hp
player.collect_item(ITEM_HEART)
player.collect_item(ITEM_HEART)
assert player.max_hp == start_max_hp + 40, player.max_hp
assert player.hp == start_hp + 40, player.hp

assert player.attack_duration == settings.PLAYER_ATTACK_DURATION
player.collect_item(ITEM_DAGGERS)
assert abs(player.attack_duration - settings.PLAYER_ATTACK_DURATION * 0.9) < 1e-9

player.collect_item(ITEM_SHIELD)
hp_before = player.hp
player.take_damage(100)
assert player.hp == hp_before - 92, player.hp  # round(100 * 0.92)

assert player.item_stacks[ITEM_CANE] == 2
assert player.item_stacks[ITEM_KNIFE] == 2

print("PLAYER STATS SMOKE TEST PASSED")
```

Run: `SDL_VIDEODRIVER=dummy PYTHONPATH=. /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python /private/tmp/claude-501/-Users-brnmarq-Documents-BrnCode-DungeonProb/82346956-d0a8-4072-8d2e-fceecf6217e7/scratchpad/smoke_player_stats.py`
Expected: FAIL before Step 3-4 are done (AttributeError on `collect_item`/`speed`/etc); PASS after.

- [ ] **Step 6: Commit**

```bash
git add src/entities/Player.py
git commit -m "Add item stack tracking and derived stats to Player"
```

---

### Task 4: Wire Player's derived stats into the ability states

**Files:**
- Modify: `src/entities/player_states/PlayingState.py`
- Modify: `src/entities/player_states/AttackState.py`
- Modify: `src/entities/player_states/ThrowState.py`
- Modify: `src/entities/player_states/RageState.py`

**Interfaces:**
- Consumes: `player.speed`, `player.get_damage(base)`, `player.attack_duration` (Task 3).
- Produces: nothing new — internal behavior change only.

- [ ] **Step 1: `PlayingState.py`**

Replace:

```python
        self.entity.vx = settings.PLAYER_SPEED * self.entity.move_direction
```

with:

```python
        self.entity.vx = self.entity.speed * self.entity.move_direction
```

- [ ] **Step 2: `AttackState.py`**

Replace, in `_update_vx`:

```python
        self.entity.vx = settings.PLAYER_SPEED * self.entity.move_direction
```

with:

```python
        self.entity.vx = self.entity.speed * self.entity.move_direction
```

Replace, in `_land_hit`:

```python
            other.take_damage(settings.PLAYER_ATTACK_DAMAGE)
```

with:

```python
            other.take_damage(self.entity.get_damage(settings.PLAYER_ATTACK_DAMAGE))
```

Replace, in `update`:

```python
        if self._elapsed >= settings.PLAYER_ATTACK_DURATION:
            self.entity.change_state("playing")
```

with:

```python
        if self._elapsed >= self.entity.attack_duration:
            self.entity.change_state("playing")
```

- [ ] **Step 3: `ThrowState.py`**

Replace, in `_update_vx`:

```python
        self.entity.vx = settings.PLAYER_SPEED * self.entity.move_direction
```

with:

```python
        self.entity.vx = self.entity.speed * self.entity.move_direction
```

(The damage-scaling change for the thrown sword itself is Task 5, not here.)

- [ ] **Step 4: `RageState.py`**

Replace, in `_update_vx`:

```python
        self.entity.vx = settings.PLAYER_SPEED * self.entity.move_direction
```

with:

```python
        self.entity.vx = self.entity.speed * self.entity.move_direction
```

Replace, in `_land_hit`:

```python
            other.take_damage(settings.PLAYER_RAGE_DAMAGE)
```

with:

```python
            other.take_damage(entity.get_damage(settings.PLAYER_RAGE_DAMAGE))
```

- [ ] **Step 5: Verify nothing broke**

Run: `SDL_VIDEODRIVER=dummy PYTHONPATH=. /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python /private/tmp/claude-501/-Users-brnmarq-Documents-BrnCode-DungeonProb/82346956-d0a8-4072-8d2e-fceecf6217e7/scratchpad/smoke_player_stats.py`
Expected: `PLAYER STATS SMOKE TEST PASSED` (still — this task doesn't change Task 3's behavior, just who reads it).

Run: `python3 -m py_compile src/entities/player_states/PlayingState.py src/entities/player_states/AttackState.py src/entities/player_states/ThrowState.py src/entities/player_states/RageState.py`
Expected: no output, exit 0.

- [ ] **Step 6: Commit**

```bash
git add src/entities/player_states/PlayingState.py src/entities/player_states/AttackState.py src/entities/player_states/ThrowState.py src/entities/player_states/RageState.py
git commit -m "Read Player's item-derived speed/damage/attack-duration in ability states"
```

---

### Task 5: Scale the thrown sword's damage by the knife's stacks

**Files:**
- Modify: `src/entities/ThrownSword.py`
- Modify: `src/entities/player_states/ThrowState.py`

**Interfaces:**
- Consumes: `player.get_damage(base)` (Task 3).
- Produces: `ThrownSword.__init__` gains a `damage: int` parameter (5th positional, before `player`); `sword.damage` — nothing outside this pair of files reads it.

- [ ] **Step 1: Accept and store damage in `ThrownSword`**

Replace the constructor signature and body:

```python
    def __init__(
        self,
        x: float,
        y: float,
        direction: int,
        damage: int,
        player: TypeVar("Player"),
        level: TypeVar("Level"),
    ) -> None:
        self.x = x
        self.y = y
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.start_x = x
        self.direction = direction
        self.damage = damage
        self.flipped = direction < 0
        self.player = player
        self.level = level
        self.is_dead = False
```

(Only the two new lines — the `damage: int` parameter and `self.damage = damage` — are additions; everything else in `__init__` is unchanged from what's already there.)

- [ ] **Step 2: Use it in `_apply_flight_damage`**

Replace:

```python
            other.take_damage(settings.PLAYER_THROW_DAMAGE)
```

with:

```python
            other.take_damage(self.damage)
```

(`_explode`'s `settings.SWORD_EXPLOSION_DAMAGE` is a separate, fixed proximity-detonation stat — deliberately not scaled by the knife; leave it untouched.)

- [ ] **Step 3: Pass the scaled damage from `ThrowState._spawn_sword`**

Replace:

```python
        sword = ThrownSword(
            entity.x + offset,
            entity.y + entity.height / 2 - ThrownSword.HEIGHT / 2,
            self.direction,
            entity,
            entity.level,
        )
```

with:

```python
        sword = ThrownSword(
            entity.x + offset,
            entity.y + entity.height / 2 - ThrownSword.HEIGHT / 2,
            self.direction,
            entity.get_damage(settings.PLAYER_THROW_DAMAGE),
            entity,
            entity.level,
        )
```

- [ ] **Step 4: Verify**

Run: `python3 -m py_compile src/entities/ThrownSword.py src/entities/player_states/ThrowState.py`
Expected: no output, exit 0.

Run: `SDL_VIDEODRIVER=dummy PYTHONPATH=. /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import settings
from src.entities.ThrownSword import ThrownSword
sword = ThrownSword(0, 0, 1, 22, object(), object())
assert sword.damage == 22
print('THROWNSWORD DAMAGE PARAM OK')
"`
Expected: `THROWNSWORD DAMAGE PARAM OK`

- [ ] **Step 5: Commit**

```bash
git add src/entities/ThrownSword.py src/entities/player_states/ThrowState.py
git commit -m "Scale thrown sword damage by the bloody knife's stacks"
```

---

### Task 6: Create the Pickup entity

**Files:**
- Create: `src/items/Pickup.py`

**Interfaces:**
- Consumes: `settings.TEXTURES["items"]`/`FRAMES["items"]` (Task 1), `src.items.definitions.ITEMS` (Task 2), `player.collect_item(item_id)` (Task 3).
- Produces: `Pickup(x, y, item_id, player, level)`, `Pickup.WIDTH`/`HEIGHT` (both `16`) — consumed by Task 7.

- [ ] **Step 1: Write the entity**

```python
"""
A stat-boosting item pickup (assets/graphics/items.png - see
src.items.definitions.ITEMS for frame indices). Duck-typed the same way
as src.entities.ThrownSword/DamageNumber (update/render/is_dead, plus
get_collision_rect) so src.map.Level's entities list needs no
special-casing. Touching the player applies its stat via
Player.collect_item and removes itself - no VFX/SFX, no respawn.
"""

from typing import Any, TypeVar

import pygame

import settings
from src.items.definitions import ITEMS


class Pickup:
    TEXTURE_ID = "items"
    WIDTH = 16
    HEIGHT = 16

    def __init__(
        self,
        x: float,
        y: float,
        item_id: str,
        player: TypeVar("Player"),
        level: TypeVar("Level"),
    ) -> None:
        self.x = x
        self.y = y
        self.width = self.WIDTH
        self.height = self.HEIGHT
        self.item_id = item_id
        self.player = player
        self.level = level
        self.is_dead = False
        self.frame_index = ITEMS[item_id]["frame_index"]

    def get_collision_rect(self) -> pygame.Rect:
        return pygame.Rect(round(self.x), round(self.y), self.width, self.height)

    def update(self, dt: float) -> None:
        if self.get_collision_rect().colliderect(self.player.get_collision_rect()):
            self.player.collect_item(self.item_id)
            self.is_dead = True

    def render(self, surface: pygame.Surface, camera: Any) -> None:
        texture = settings.TEXTURES[self.TEXTURE_ID]
        frame = settings.FRAMES[self.TEXTURE_ID][self.frame_index]
        image = pygame.Surface((frame.width, frame.height), pygame.SRCALPHA)
        image.fill((0, 0, 0, 0))
        image.blit(texture, (0, 0), frame)

        dest = camera.apply(pygame.Rect(self.x, self.y, self.width, self.height))
        surface.blit(image, dest)
```

- [ ] **Step 2: Verify with a headless smoke test**

Run: `SDL_VIDEODRIVER=dummy PYTHONPATH=. /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame
pygame.display.set_mode((1, 1))

import settings
from src.map.Level import Level
from src.entities.Player import Player
from src.items.definitions import ITEM_CANE
from src.items.Pickup import Pickup

level = Level(settings.TILEMAPS['forest'])
player = Player(16, 100, level)
pickup = Pickup(player.x, player.y, ITEM_CANE, player, level)
assert not pickup.is_dead
pickup.update(0.016)
assert pickup.is_dead
assert player.item_stacks[ITEM_CANE] == 1
print('PICKUP SMOKE TEST PASSED')
"`
Expected: `PICKUP SMOKE TEST PASSED`

- [ ] **Step 3: Commit**

```bash
git add src/items/Pickup.py
git commit -m "Add Pickup entity for stat-boosting items"
```

---

### Task 7: Spawn the five test pickups at the end of the map

**Files:**
- Modify: `src/states/PlayState.py`

**Interfaces:**
- Consumes: `Pickup(x, y, item_id, player, level)` (Task 6), `src.items.definitions.ITEMS` (Task 2), `Level.ground_row(col)` (existing, same helper `_spawn_demon` uses).
- Produces: nothing new — `PlayState.enter()` now populates 5 additional `level.entities`.

- [ ] **Step 1: Add the imports**

In `src/states/PlayState.py`, replace:

```python
from src.entities.Player import Player
from src.entities.SmallDemon import SmallDemon
from src.map.Level import Level
```

with:

```python
from src.entities.Player import Player
from src.entities.SmallDemon import SmallDemon
from src.items.definitions import ITEMS
from src.items.Pickup import Pickup
from src.map.Level import Level
```

- [ ] **Step 2: Add `_spawn_test_items`**

Add this method to `PlayState`, near `_spawn_demon`:

```python
    def _spawn_test_items(self) -> None:
        """One of each item (src.items.definitions.ITEMS), standing on
        ground at the end of the map, one tile apart - for manually
        testing pickups. Not a real drop table; see the design spec's
        Non-goals.
        """
        tile_width = self.level.tilemap.tile_width
        last_col = self.level.tilemap.cols - 1
        for offset, item_id in enumerate(ITEMS.keys()):
            col = last_col - offset
            row = self.level.ground_row(col)
            if row is None:
                continue

            x = col * tile_width
            y = row * self.level.tilemap.tile_height - Pickup.HEIGHT
            self.level.entities.append(Pickup(x, y, item_id, self.player, self.level))
```

- [ ] **Step 3: Call it from `enter()`**

Replace:

```python
        self.hud = HUD(self.player)
```

with:

```python
        self.hud = HUD(self.player)
        self._spawn_test_items()
```

- [ ] **Step 4: Verify**

Run: `python3 -m py_compile src/states/PlayState.py`
Expected: no output, exit 0.

Run: `SDL_VIDEODRIVER=dummy PYTHONPATH=. /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python -c "
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame
pygame.display.set_mode((1, 1))

from src.states.PlayState import PlayState
from src.items.Pickup import Pickup

state = PlayState()
state.enter()
pickups = [e for e in state.level.entities if isinstance(e, Pickup)]
assert len(pickups) == 5, pickups
print('PLAYSTATE SPAWN SMOKE TEST PASSED')
"`
Expected: `PLAYSTATE SPAWN SMOKE TEST PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/states/PlayState.py
git commit -m "Spawn one of each item pickup at the end of the map"
```

---

### Task 8: End-to-end smoke test and manual run

**Files:**
- None (verification-only task).

**Interfaces:**
- Consumes: everything from Tasks 1-7.
- Produces: nothing — confirms the whole feature works together before calling it done.

- [ ] **Step 1: Write the end-to-end headless script**

Save as `/private/tmp/claude-501/-Users-brnmarq-Documents-BrnCode-DungeonProb/82346956-d0a8-4072-8d2e-fceecf6217e7/scratchpad/smoke_items_e2e.py`:

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
pygame.display.set_mode((1, 1))

import settings
from src.states.PlayState import PlayState
from src.items.Pickup import Pickup
from src.items.definitions import ITEM_CANE, ITEM_HEART, ITEM_KNIFE, ITEM_SHIELD, ITEM_DAGGERS

state = PlayState()
state.enter()

pickups = [e for e in state.level.entities if isinstance(e, Pickup)]
assert len(pickups) == 5

player = state.player
start_speed = player.speed
start_max_hp = player.max_hp

for pickup in list(pickups):
    player.x, player.y = pickup.x, pickup.y
    state.level.update(0.016)

assert player.item_stacks[ITEM_CANE] == 1
assert player.item_stacks[ITEM_HEART] == 1
assert player.item_stacks[ITEM_KNIFE] == 1
assert player.item_stacks[ITEM_SHIELD] == 1
assert player.item_stacks[ITEM_DAGGERS] == 1

assert player.speed > start_speed
assert player.max_hp == start_max_hp + settings.ITEM_HP_BONUS
assert player.get_damage(settings.PLAYER_ATTACK_DAMAGE) > settings.PLAYER_ATTACK_DAMAGE
assert player.attack_duration < settings.PLAYER_ATTACK_DURATION

remaining_pickups = [e for e in state.level.entities if isinstance(e, Pickup)]
assert remaining_pickups == [], remaining_pickups

print("END-TO-END ITEM PICKUP SMOKE TEST PASSED")
```

- [ ] **Step 2: Run it**

Run: `SDL_VIDEODRIVER=dummy PYTHONPATH=. /Users/brnmarq/.pyenv/versions/3.14.7/envs/game-programming/bin/python /private/tmp/claude-501/-Users-brnmarq-Documents-BrnCode-DungeonProb/82346956-d0a8-4072-8d2e-fceecf6217e7/scratchpad/smoke_items_e2e.py`
Expected: `END-TO-END ITEM PICKUP SMOKE TEST PASSED`

- [ ] **Step 3: Manual run via the `run` skill**

Launch the game for real (not headless) and confirm visually: the 5 items render at the end of the map with their white outline intact, walking into each one removes it, and nothing crashes. Use the project's `run` skill (or `python main.py` directly) to drive this — walk the player to the far end of the forest map and touch all 5 pickups.

- [ ] **Step 4: Nothing to commit**

This task is verification-only — the scratch scripts live outside the repo (`/private/tmp/.../scratchpad/`) and are not committed. If Task 8 surfaces a bug, fix it in the relevant task's files and re-run Steps 1-2 of this task before considering the feature done.
