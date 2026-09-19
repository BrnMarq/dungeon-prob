# Dungeon Prob

A 2D medieval-themed action-platformer roguelike inspired by **Risk of
Rain 1**, built with [gale-engine](https://pypi.org/project/gale-engine/)
(a lightweight game framework on top of Pygame).

**Status: playable end to end.** A run starts at the title screen, drops
you into the forest, scales its difficulty as the clock runs, and ends
either at the game-over screen or on the victory screen after you beat
the zone guardian. Everything documented below is in the tree today; see
[CHANGELOG.md](CHANGELOG.md) for the history behind it.

## Core loop

Fight the demons that keep spawning, spend the gold they drop on chests,
stack the items those chests pay out, and survive a difficulty that
climbs on a timer. When you are ready, activate the level's altar: it
doubles the spawn rate for 90 seconds, and when that runs out the altar
gives you a choice - reset the forest for another lap of item farming, or
summon the zone guardian and fight for the run. Beating the guardian ends
the run.

## Running it

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key(s)      | Action                                                     |
| ----------- | ---------------------------------------------------------- |
| `A` / `←`   | Move left                                                  |
| `D` / `→`   | Move right                                                 |
| `Space`     | Jump (fixed height)                                        |
| `↑` / `↓`   | Climb up/down, while touching a vine                       |
| `Q`         | Attack - front-facing melee swing                          |
| `W`         | Throw sword - projectile that lands and can be detonated   |
| `E`         | Dash - gravity-cancelling burst, grants invincibility      |
| `R`         | Rage - invincible burst damaging everything around you     |
| `F`         | Interact - open a chest, use the altar                     |
| `G`         | Reset the level, at an altar whose buff has ended          |
| `Enter`     | Start (title screen) / play again (game-over, victory)     |
| `Esc`       | Open/close the pause menu                                  |

`Q`/`W`/`E`/`R` map 1:1 to the four HUD ability slots, each of which
shows its own key letter and a live cooldown sweep.

## Abilities

| Ability | Key | Damage | Cooldown | Notes |
| ------- | --- | ------ | -------- | ----- |
| Attack  | `Q` | 15     | none     | 20px reach in front, 0.3s swing; rooted on the ground, but keeps air control mid-air |
| Throw   | `W` | 15     | 4s       | Flies, then floats where it lands; touch it to detonate for 20 damage in a 48px radius, which also refunds your dash |
| Dash    | `E` | -      | 3s       | 320px/s for 0.25s, cancels gravity, and grants 1s of invincibility (the HUD hp bar turns white) |
| Rage    | `R` | 10 x 4 | 8s       | 1s of invincibility, hitting everything within 64px four times |

## Progression

- **Health**: 100 to start. `Player.heal()` is the only thing that gives
  it back - it caps at your maximum and floats a green `+N` above your
  head. Damage taken floats in purple; a dodge shows "Dodged!".
- **Gold**: 5 per demon, scaled by the difficulty tier's reward
  multiplier. Spent at chests.
- **XP and levels**: 10 per demon, also reward-scaled. Each level needs
  1.5x the XP of the last and grants +10 maximum HP and +2 base damage.
  Levelling raises the ceiling only - it does not heal you.

## Items

Twelve items, every one of which stacks with itself. Chests roll from the
common pool 90% of the time and the rare (red) pool 10%.

| Item | Pool | Effect per stack |
| ---- | ---- | ---------------- |
| Walking Cane  | common | +10% movement speed |
| Frozen Heart  | common | +20 maximum HP, and heals that much immediately |
| Bloody Knife  | common | +10% damage |
| Aegis Shield  | common | Incoming damage x0.92 (compounding, never reaches 0) |
| Short Daggers | common | Attack duration x0.9 (compounding, floored at 0.05s) |
| Hunter's Hat  | common | +5% critical chance; crits deal double damage |
| Cat's Spirit  | common | +5% dodge chance, capped at 75% |
| Loadstone     | common | Cooldowns x0.9 (compounding, floored at 0.2x) |
| Blood Thirst  | rare   | Every landed crit cuts 0.25s off your cooldowns |
| Samurai Sword | rare   | +5% chance any landed hit triggers a rage-style burst, capped at 50% |
| Jimbo         | rare   | x4 damage while owned (does not stack further) |
| Soul Box      | rare   | +1 base damage per kill, permanently |

Picking one up floats its name above the pickup, tinted by rarity, and
adds it to the translucent item bar in the HUD's bottom-left corner -
every item you are carrying, with its stack count, without leaving the
run to check.

## The run

### Difficulty tiers

The tier advances on elapsed run time and never goes back down. It scales
enemy health, enemy damage, kill rewards, and how often demons spawn. The
current tier's name and color show on the HUD's run-timer signpost, which
also fills over a 20-minute run.

| Tier | From | Spawn every | Enemy HP | Enemy damage | Rewards |
| ---- | ---- | ----------- | -------- | ------------ | ------- |
| Easy      | 0:00  | 4.0s | x1.0 | x1.0 | x1.0 |
| Medium    | 3:00  | 3.0s | x1.3 | x1.2 | x1.3 |
| Hard      | 6:00  | 2.5s | x1.6 | x1.4 | x1.6 |
| Very Hard | 10:00 | 2.0s | x2.0 | x1.6 | x2.0 |

### Enemies

**Small demon** - 40 HP, 10 damage, both tier-scaled at spawn. Chases you
horizontally, jumps over anything in its way, climbs vines to reach you,
and attacks in melee range. Staggers when hurt, and shows an overhead
health bar once damaged. They spawn on standable ground just off-screen
beside you, drawn evenly from either side.

### Chests

Six to eight per level, at points the map defines. Opening one costs gold
(20 base, scaled by the tier's reward multiplier, so they get pricier as
rewards grow) and pays out a random item shortly after the lid opens -
long enough that you can walk away and come back for it later.

### The altar

One per level. Activating it (`F`) fully heals you, swaps the music, and
starts a 90-second buff that halves the spawn interval - roughly twice
the monsters. When the buff ends, spawning stops entirely and the altar
offers two choices:

- **`F` - Summon Guardian**: the zone guardian appears, and the run is
  decided by that fight.
- **`G` - Reset Level**: regenerates the forest - fresh chests, a fresh
  dormant altar, you back at the spawn point - while keeping your run
  time, difficulty tier, gold, XP, level, items and health. This is the
  farming lap, and it is the intended way to get strong enough for the
  guardian.

### The guardian: The Reaper

1200 HP and 25/30/40 damage per attack, all tier-scaled at summon time.
It floats - no gravity, no tile collision - drifting toward a hover point
beside you, and it has no hurt animation, so it cannot be stun-locked out
of a wind-up the way a demon can. Its attacks:

- **Magic cast** - drops a detonation on wherever you were standing,
  telegraphed by a growing ring you can walk out of.
- **Teleport** - vanishes, reappears beside you, and swings immediately.
- **Scythe swipe** - fast, close range.
- **Long sweep** - slow, heavily telegraphed, and reaches most of a
  screen-width.

Its health shows on a bar across the top of the screen, and summoning it
switches the music to its own track. Beat it and the run ends on the
victory screen, which totals your time, kills, gold,
damage dealt, and every item you collected.

## Pause, save and load

`Esc` opens the pause menu from any screen - Resume, Save, Load, Quit.
Saving is available while playing and writes a single slot; loading works
from anywhere and replaces whatever is on screen with the saved run. A
save captures your full stats and position, every live demon, every chest
(cost, open state, its pending item roll), every dropped-but-uncollected
item, the altar's phase and remaining buff, and the guardian fight if one
is in progress. Short-lived effects and projectiles are not saved.

## Architecture

The repository follows the standard `gale` project layout:

```text
├── assets/
│   ├── fonts/            # TrueType / OpenType font files (.ttf)
│   ├── graphics/         # Spritesheets, textures, tilesets (.png)
│   │   └── boss/         # The Reaper's sheet and its slash/disappear effects
│   ├── maps/             # Tiled exported JSON maps and tileset data
│   └── sounds/           # Sound effects (.wav) and music (.mp3)
├── src/
│   ├── entities/         # Player, enemies, boss, world pickups, effects
│   │   ├── player_states/  # Playing, Attack, Throw, Dash, Rage, Climb
│   │   ├── enemy_states/   # Spawn, Idle, Follow, Climb, Attack, Hurt, Dead
│   │   ├── boss_states/    # Appear, Float, Magic, Teleport, Swing, Death
│   │   └── mixins/         # Drawable / Animated / Collidable
│   ├── items/            # Item registry and the world Pickup entity
│   ├── map/              # Tiled JSON level loading and parallax background
│   ├── states/           # Title, Play, PauseMenu, GameOver, Victory
│   ├── ui/               # HUD, enemy and boss health bars, interact prompts
│   ├── audio.py          # Cross-fading music and sound-effect playback
│   ├── Camera.py         # 2D scrolling camera, bounded to the level
│   ├── commands.py       # Input-bound Command classes
│   ├── render.py         # Shared sprite/outline cache and fast alpha blitting
│   └── Game.py           # Primary game orchestrator / entry wrapper
├── CHANGELOG.md          # Chronological log of versions, features, and fixes
├── CLAUDE.md             # AI assistant guidance and project context
├── main.py               # Application entrypoint
└── settings.py           # Screen dimensions, tuning constants, asset registry
```

A few conventions worth knowing before changing anything:

- **`settings.py` is the single place** tuning constants (speeds, damage,
  cooldowns, colors, key bindings) and asset registrations (`TEXTURES`,
  `FRAMES`, `TILEMAPS`, `SOUNDS`, `MUSIC`) live. Most gameplay tweaks
  start and end there.
- **Entities drive behavior through per-entity state machines.** Anything
  living on the tilemap subclasses `Entity` and supplies its own states
  and animation definitions.
- **Short-lived effects are duck-typed, not subclassed.** Floating text,
  slashes and explosions only implement `update`/`render`/`is_dead`, so
  they drop into a level's entity list with no special-casing.
- **Every alpha blit goes through `src/render.py`**, which caches sprites
  and composites through SDL2's own blitter - see its module docstring
  for why that matters on some platforms.

See [CHANGELOG.md](CHANGELOG.md) for the full, detailed history.

## Special thanks

None of the art or audio in this game is mine. Everything under
`assets/` comes from one of the packs below, used under its own license -
my thanks to the people who made them and gave them away.

### Art

- **[Mini Legend - Asset Pack](https://alwaysrice.itch.io/mini-legend)**
  by AlwaysRice - the 16x16 forest tileset, the parallax treeline and
  foliage, the player character, the small demon, and the props dotted
  around the level.
- **[Mini Legend - Small Cave](https://alwaysrice.itch.io/mini-legend-cave)**
  by AlwaysRice - The Reaper, the zone guardian, along with the slash
  effects its scythe leaves behind.

### Sound effects

- **[400 Sounds Pack](https://ci.itch.io/400-sounds-pack)** by
  Chequered Ink
- **[Free Fantasy 200 SFX Pack](https://tommusic.itch.io/free-fantasy-200-sfx-pack)**
  by TomMusic

Between them they cover every effect in `assets/sounds/` - the swings,
the dash, the chest, the pickups, and the hits.

### Music

- **[Medieval Free Soundtrack (No Copyright)](https://alkakrab.itch.io/free-medieval-soundtrack-no-copyright)**
  by alkakrab - every track in the game: the title screen, the forest,
  the altar, the boss fight, and both endings. It is released under CC0
  and asks for no credit at all, which makes giving it the very least I
  can do.
