# Item pickups (stat-boosting stackables) — design

## Summary

A pickup/effects subsystem under `src/items/`, matching the layout
CLAUDE.md already reserves for it ("Item definitions, modifiers,
stacking logic, effects registry"). Five items ship with this pass,
sprited on `assets/graphics/items.png` (80×16, five 16×16 icons with a
baked-in white outline — no outline rendering needed):

| # | Item | Sprite frame | Effect per stack |
|---|------|--------------|-------------------|
| 0 | Walking cane | 0 | +10% move speed |
| 1 | Frozen heart | 1 | +20 max HP (heals on pickup too) |
| 2 | Bloody knife | 2 | +10% damage multiplier |
| 3 | Aegis shield | 3 | ×0.92 damage taken, compounding |
| 4 | Short daggers | 4 | −10% attack duration (floor 0.05s) |

Items stack: picking up a second of the same type adds another
increment of its effect (RoR1-style, per the project's stated
inspiration in CLAUDE.md). This pass spawns one of each near the end
of the map for manual testing; a real drop-table/spawn-budget system
is a separate future piece of work.

## Non-goals (this pass)

- No HUD/inventory display of held items.
- No pickup VFX/SFX (plain despawn on touch, like walking over it).
- No drop tables, rarity, or random spawn logic — fixed test spawn only.
- No re-timing of the attack animation's frame interval when attack
  speed changes (see Attack duration below) — a future item-visuals
  pass can revisit if the mismatch reads as jank in practice.

## Components

### `src/items/definitions.py`

A plain registry, the "effects registry" CLAUDE.md's architecture
section names:

```python
ITEM_CANE = "cane"
ITEM_HEART = "heart"
ITEM_KNIFE = "knife"
ITEM_SHIELD = "shield"
ITEM_DAGGERS = "daggers"

ITEMS = {
    ITEM_CANE:    {"frame_index": 0},
    ITEM_HEART:   {"frame_index": 1},
    ITEM_KNIFE:   {"frame_index": 2},
    ITEM_SHIELD:  {"frame_index": 3},
    ITEM_DAGGERS: {"frame_index": 4},
}
```

Frame index is all a definition needs — the *effect* of each item is
resolved by `Player.collect_item` (below) keying on item id, not by
data in this dict, since each effect touches a different Player stat
in a different way (additive vs. multiplicative vs. compounding) and
forcing that into a generic shape would be more machinery than five
items justifies. If a sixth item needs a genuinely generic "modify
stat X by Y" shape, that's the point to generalize — not before.

### `src/items/Pickup.py`

Duck-typed entity, same shape as `ThrownSword`/`DamageNumber` (the
`src.map.Level.entities` list only ever needs `update`/`render`/
`is_dead`, plus `get_collision_rect` for the debug overlay and touch
detection):

```python
class Pickup:
    TEXTURE_ID = "items"
    WIDTH = 16
    HEIGHT = 16

    def __init__(self, x, y, item_id, player, level): ...
    def get_collision_rect(self) -> pygame.Rect: ...
    def update(self, dt) -> None:
        # touches player's rect -> player.collect_item(item_id); is_dead = True
    def render(self, surface, camera) -> None: ...
```

Rendering blits `FRAMES["items"][frame_index]` from `TEXTURES["items"]`
the same way `DrawableMixin`/`ThrownSword.render` already do — no
flip, no offset, no outline pass (baked into the art).

### `Player` changes

- `self.item_stacks: Counter[str] = Counter()` — stack count per item id.
- `collect_item(item_id: str) -> None` — increments the counter and,
  for `heart` only, immediately applies `max_hp`/`hp` (the other four
  are pure derived-property reads, computed on demand below, so
  there's nothing to "apply" for them beyond the stack count going up).
- `speed` (property): `settings.PLAYER_SPEED * (1 + 0.10 * stacks[cane])`.
  Replaces the raw `settings.PLAYER_SPEED` read in every state's
  `_update_vx`/`PlayingState.update` (dash is a fixed burst, not
  "movement speed," and stays on `settings.PLAYER_DASH_SPEED`
  untouched).
- `get_damage(base: float) -> int`: `round(base * (1 + 0.10 *
  stacks[knife]))`. Used by `AttackState._land_hit`,
  `RageState._land_hit`, and by `ThrowState` when spawning a
  `ThrownSword` (passed in and stored as `sword.damage`, replacing the
  sword's current hardcoded `settings.PLAYER_THROW_DAMAGE` reads in
  `_apply_flight_damage`/`_explode`).
- `attack_duration` (property): `max(0.05, settings.PLAYER_ATTACK_DURATION
  * (0.9 ** stacks[daggers]))`. `AttackState.update` compares elapsed
  time against this instead of the raw setting. The attack animation's
  frame interval (set once at `Player.__init__` from the base
  setting) does **not** retime — see Non-goals.
- `take_damage` multiplies incoming `amount` by `0.92 **
  stacks[shield]` before applying (compounding, not additive — no
  cap needed since it asymptotically approaches, never reaches, zero).

### Spawning (`src/states/PlayState.py`)

`_spawn_test_items()`, called once from `enter()` alongside the
player/camera/HUD setup:

```python
def _spawn_test_items(self) -> None:
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

One tile apart, standing on solid ground, same `ground_row` helper
`_spawn_demon` already relies on — walking to the end of the map lets
you pick up all five in a row.

### `settings.py`

- `TEXTURES["items"]` / `FRAMES["items"]` registration (16×16 cells,
  matching the `marze`/`dark_sword` pattern already in the file).
- Per-stack constants: `ITEM_SPEED_BONUS = 0.10`, `ITEM_HP_BONUS =
  20`, `ITEM_DAMAGE_BONUS = 0.10`, `ITEM_RESISTANCE_FACTOR = 0.92`,
  `ITEM_ATTACK_SPEED_FACTOR = 0.9`, `ITEM_ATTACK_DURATION_FLOOR =
  0.05`.

## Data flow

1. `PlayState.enter()` spawns 5 `Pickup` entities into `level.entities`.
2. Each frame, `Level.update` calls `Pickup.update`, which checks
   collision against the player's rect.
3. On touch: `player.collect_item(item_id)` bumps the stack counter
   (and, for hearts, heals); the pickup marks itself `is_dead` and
   `Level.update`'s existing dead-entity filter removes it next frame.
4. Every subsequent read of `player.speed` / `player.get_damage(...)`
   / `player.attack_duration` / `player.take_damage(...)` reflects the
   new stack count immediately — no caching, no explicit "recompute"
   step, since these are plain properties/methods over the counter.

## Testing

No test suite exists in this project (verified — no `test*` paths
under the repo). Verification is a headless smoke script (SDL dummy
driver, same approach used for the R-ability work earlier this
session): spawn a `Player` and one `Pickup` of each type on a real
level, walk the player into each, and assert `speed`/`get_damage`/
`attack_duration`/post-`take_damage` HP match the expected per-stack
formulas; also assert a second pickup of the same `item_id` stacks
(doubles the bonus) rather than being a no-op. Then a manual run via
the `run` skill to confirm the sprites render with their outline
intact and pickup-on-touch feels right in the actual window.
