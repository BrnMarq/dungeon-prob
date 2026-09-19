# Dungeon Prob

A 2D medieval-themed action-platformer roguelike inspired by **Risk of
Rain 1**, built with [gale-engine](https://pypi.org/project/gale-engine/)
(a lightweight game framework on top of Pygame).

**Status: `v0.1.0`, first playable build.** Movement, jump, dash, and a
melee attack all work, and one enemy (the small demon) spawns, chases,
fights back, and dies. Most of the systems below - items, difficulty
tiers, the beacon/guardian loop, real title/pause/victory screens - are
still unbuilt; see [CHANGELOG.md](CHANGELOG.md) for exactly what exists
today.

## Core loop (target design)

Combat hordes of medieval monsters, survive scaling difficulty tiers over
time, collect randomized items that stack and grant passive/active stats
or procedural effects, locate the level beacon/portal, defeat the zone
guardian, and advance.

## Running it

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key(s)          | Action                          |
| --------------- | -------------------------------- |
| `A` / `←`        | Move left                        |
| `D` / `→`        | Move right                       |
| `Space`          | Jump (fixed height)              |
| `Q`              | Attack (front-facing melee)      |
| `W`              | *Ability slot 2 - not implemented yet* |
| `E`              | Dash (brief invincibility + speed burst) |
| `R`              | *Ability slot 4 - not implemented yet* |
| `Esc`            | Quit                              |

The four ability keys (`Q`/`W`/`E`/`R`) map 1:1 to the four HUD ability
slots at the bottom of the screen.

## Architecture

The repository follows the standard `gale` project layout:

```text
├── assets/
│   ├── fonts/           # TrueType / OpenType font files (.ttf)
│   ├── graphics/        # Spritesheets, textures, tilesets (.png)
│   ├── maps/            # Tiled exported JSON maps and tileset data (.json, .tsj, .tmj)
│   └── sounds/          # Sound effects (.wav) and music (.ogg)
├── src/
│   ├── entities/        # Player, enemies, and their per-entity state machines
│   ├── map/             # Tiled JSON parser, Tilemap loader, collision layers
│   ├── states/           # Gale StateMachine states (Title, Play, Pause, GameOver, Victory)
│   ├── ui/               # HUD (health, cooldowns, ability bar) and health bars
│   ├── Camera.py         # 2D scrolling camera tracking the player within level bounds
│   ├── commands.py       # Input-bound Command classes (move, jump, dash, attack)
│   └── Game.py           # Primary game orchestrator / entry wrapper
├── CHANGELOG.md          # Chronological log of versions, features, and bug fixes
├── CLAUDE.md             # AI assistant guidance and project context
├── main.py               # Application entrypoint
└── settings.py           # Screen dimensions, virtual resolution, asset registry, inputs
```

`settings.py` is the single place tuning constants (speeds, cooldowns,
colors, key bindings) and asset registrations (`TEXTURES`, `FRAMES`,
`TILEMAPS`) live - most gameplay tweaks start there.

## Current gameplay features

- **Movement**: run/idle animations, fixed-height jump.
- **Dash** (`E`): a short gravity-cancelling burst with a cooldown, and
  grants 1 second of invincibility (shown as a white "INVINCIBLE" HUD bar).
- **Melee attack** (`Q`): a 3-frame front-facing swing with a hitbox that
  deals damage; rooted on the ground, but keeps air control mid-air.
- **Small demon enemy**: spawns randomly within a configurable range of
  the player, chases, attacks in melee range, reacts to damage
  (hurt/death animations), and shows an overhead health bar once
  damaged.
- **HUD**: HP bar, XP bar, level badge, and a 4-slot ability bar with
  live cooldown timers.

See [CHANGELOG.md](CHANGELOG.md) for the full, detailed history.
