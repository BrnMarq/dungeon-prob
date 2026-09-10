# CLAUDE.md - Development & Architecture Guide

## Project Overview

This project is a 2D medieval-themed action-platformer roguelike inspired by **Risk of Rain 1**.

- **Core Loop**: Combat hordes of medieval monsters, survive scaling difficulty tiers over time, collect randomized items that stack and grant passive/active stats or procedural effects, locate the level beacon/portal, defeat the zone guardian, and advance.
- **Engine**: Built with **`gale-engine`** (a lightweight game development framework built on top of **Pygame**).
- **Map System**: Levels and tile colliders are loaded from **Tiled JSON** (`.json`) exported maps.

---

## Architecture & Directory Structure

The repository strictly adheres to the standard `gale` project layout:

```text
├── assets/
│   ├── fonts/           # TrueType / OpenType font files (.ttf)
│   ├── graphics/        # Spritesheets, textures, tilesets (.png)
│   ├── maps/            # Tiled exported JSON maps and tileset data (.json, .tsj, .tmj)
│   └── sounds/          # Sound effects (.wav) and music (.ogg)
├── src/
│   ├── entities/        # Player, Enemies, Bosses, Combat Hurtboxes/Hitboxes
│   ├── items/           # Item definitions, modifiers, stacking logic, effects registry
│   ├── map/             # Tiled JSON parser, Tilemap loader, collision layers
│   ├── states/          # Gale StateMachine states (Title, Play, Pause, GameOver, Victory)
│   │   ├── BaseState.py
│   │   ├── PlayState.py
│   │   ├── TitleState.py
│   │   └── ...
│   ├── ui/              # HUD (health, cooldowns, item inventory bar, difficulty timer)
│   ├── Camera.py        # 2D scrolling camera tracking the player within level boundaries
│   └── Game.py          # Primary game orchestrator / entry wrapper
├── CHANGELOG.md         # Chronological log of versions, features, and bug fixes
├── CLAUDE.md            # AI assistant guidance and project context (this file)
├── main.py              # Application entrypoint
├── README.md            # Detailed game manual, architecture overview, and setup guide
└── settings.py          # Screen dimensions, virtual resolution, asset registry, inputs
```
