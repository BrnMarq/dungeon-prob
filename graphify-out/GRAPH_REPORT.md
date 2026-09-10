# Graph Report - DungeonProb  (2026-09-10)

## Corpus Check
- Corpus is ~999 words - fits in a single context window. You may not need a graph.

## Summary
- 91 nodes · 109 edges · 19 communities (9 shown, 4 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.88)
- Token cost: 0 input · 66,688 output

## Community Hubs (Navigation)
- Directory Architecture
- Gale StateMachine
- Game Orchestrator
- Game Over State
- Pause State
- Play State
- Title State
- Victory State
- Tech Stack & Overview
- Settings Config
- Sprite Asset
- Changelog
- README

## God Nodes (most connected - your core abstractions)
1. `DungeonProb` - 13 edges
2. `BaseState` - 12 edges
3. `GameOverState` - 9 edges
4. `PauseState` - 9 edges
5. `PlayState` - 9 edges
6. `TitleState` - 9 edges
7. `VictoryState` - 9 edges
8. `src/` - 8 edges
9. `src/states/ (Gale StateMachine)` - 5 edges
10. `gale-engine` - 3 edges

## Surprising Connections (you probably didn't know these)
- `DungeonProb` --uses--> `GameOverState`  [INFERRED]
  src/Game.py → src/states/GameOverState.py
- `DungeonProb` --uses--> `PauseState`  [INFERRED]
  src/Game.py → src/states/PauseState.py
- `DungeonProb` --uses--> `PlayState`  [INFERRED]
  src/Game.py → src/states/PlayState.py
- `DungeonProb` --uses--> `TitleState`  [INFERRED]
  src/Game.py → src/states/TitleState.py
- `DungeonProb` --uses--> `VictoryState`  [INFERRED]
  src/Game.py → src/states/VictoryState.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Gale StateMachine Pattern** — claude_states, src_states_basestate, src_states_playstate, src_states_titlestate, src_game [INFERRED 0.85]
- **gale-engine Technology Stack** — claude_gale_engine, claude_pygame, requirements_gale_engine [EXTRACTED 1.00]

## Communities (19 total, 4 thin omitted)

### Community 0 - "Directory Architecture"
Cohesion: 0.20
Nodes (9): Camera, Architecture & Directory Structure, assets/, src/entities/, src/items/, src/map/, src/, src/ui/ (HUD) (+1 more)

### Community 1 - "Gale StateMachine"
Cohesion: 0.47
Nodes (3): src/states/ (Gale StateMachine), GaleBaseState, BaseState

### Community 2 - "Game Orchestrator"
Cohesion: 0.20
Nodes (5): Game, InputListener, DungeonProb, InputData, Surface

### Community 3 - "Game Over State"
Cohesion: 0.22
Nodes (4): GameOverState, Any, InputData, Surface

### Community 4 - "Pause State"
Cohesion: 0.22
Nodes (4): PauseState, Any, InputData, Surface

### Community 5 - "Play State"
Cohesion: 0.22
Nodes (4): PlayState, Any, InputData, Surface

### Community 6 - "Title State"
Cohesion: 0.22
Nodes (4): Any, InputData, Surface, TitleState

### Community 7 - "Victory State"
Cohesion: 0.22
Nodes (4): Any, InputData, Surface, VictoryState

### Community 8 - "Tech Stack & Overview"
Cohesion: 0.40
Nodes (5): gale-engine, DungeonProb Project Overview, Pygame, Tiled JSON Map System, gale-engine==1.16.0 dependency

## Knowledge Gaps
- **11 isolated node(s):** `Pygame`, `Tiled JSON Map System`, `assets/`, `src/entities/`, `src/items/` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 52 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DungeonProb` connect `Game Orchestrator` to `Gale StateMachine`, `Game Over State`, `Pause State`, `Play State`, `Title State`, `Victory State`?**
  _High betweenness centrality (0.212) - this node is a cross-community bridge._
- **Why does `GameOverState` connect `Game Over State` to `Gale StateMachine`, `Game Orchestrator`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Why does `PauseState` connect `Pause State` to `Gale StateMachine`, `Game Orchestrator`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `DungeonProb` (e.g. with `GameOverState` and `PauseState`) actually correct?**
  _`DungeonProb` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Pygame`, `Tiled JSON Map System`, `assets/` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._