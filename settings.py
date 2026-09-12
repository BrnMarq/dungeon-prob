"""
Every setting here overrides gale.conf.global_settings' default for
gale.game.Game -- anything you remove (or never had) falls back to
gale's own default automatically; see gale.conf for the full list.
You can also add settings of your own here (for instance PLAYER_SPEED)
and read them back the same way, with `from gale.conf import settings`.
"""

import pathlib

import pygame

from gale import frames
from gale import input_handler

# No need to call pygame.mixer.init()/pygame.font.init() here: importing
# anything under gale (frames/input_handler above, for instance) already
# calls pygame.init(), which initializes every subsystem pygame ships
# with, mixer and font included -- and does so without raising if, say,
# no audio device is available, unlike calling pygame.mixer.init() directly.

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, "quit")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, "move_right")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, "move_left")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, "jump")
input_handler.InputHandler.set_keyboard_action(
    input_handler.KEY_h, "toggle_debug_hitboxes"
)

# Ability bar - Q/W/E/R map straight to HUD slots 1-4 (src.ui.HUD). Q and E
# are wired to real abilities below; W/R are reserved action ids with
# nothing bound to them on the receiving end yet (src.entities.Player) -
# safe no-ops until those abilities exist.
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_q, "attack")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_w, "ability_2")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_e, "dash")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_r, "ability_4")

TITLE = "Dungeon Prob"

# Size we want to emulate
VIRTUAL_WIDTH = 640
VIRTUAL_HEIGHT = 360

# Size of our actual window
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

BASE_DIR = pathlib.Path(__file__).parent

# Used by src.entities.Entity for gravity and by Level-driven entities in
# general - tune to taste once combat/platforming feel is being dialed in.
GRAVITY = 980

# Rate at which gale.camera.Camera.follow() eases toward its target - see
# src/Camera.py and how PlayState wires up the camera to follow the player.
CAMERA_FOLLOW_RATE = 8.0

PLAYER_SPEED = 80

# Variable-height jump: the takeoff speed is always the same (full arc if
# held), but releasing "jump" early while still ascending clamps vy up to
# JUMP_CUT_VELOCITY (a smaller upward speed), so the arc peaks sooner and
# lower. The longer the button stays held, the closer the jump gets to
# its full height.
JUMP_TAKEOFF_SPEED = GRAVITY / 3
JUMP_CUT_VELOCITY = GRAVITY / 8

# Dash: a short, gravity-cancelling horizontal burst - see
# src.entities.player_states.DashState. Duration matches the 7-frame dash
# animation (Marze.png row 2) so the streak frames play out over the burst.
PLAYER_DASH_SPEED = 320
PLAYER_DASH_DURATION = 0.25
PLAYER_DASH_COOLDOWN = 3

# Front-facing melee attack (Q ability) - src.entities.player_states.AttackState.
# No dedicated sprite yet, so it plays the idle animation for its duration
# instead - see AttackState for the hit-frame timing this implies.
PLAYER_ATTACK_RANGE = 20
PLAYER_ATTACK_DAMAGE = 15
PLAYER_ATTACK_DURATION = 0.3

# Used by src.entities.enemy_states.FollowState/AttackState.
DEMON_SPEED = 40
DEMON_ATTACK_RANGE = 24
# How long the demon stands idle after its attack animation finishes before
# resuming the chase - on top of the attack animation's own runtime.
DEMON_ATTACK_COOLDOWN = 0.6
DEMON_ATTACK_DAMAGE = 10
DEMON_MAX_HP = 40

# Overhead enemy health bar (src/ui/health_bar.py, drawn from
# src.map.Level.render for any entity with SHOW_HEALTH_BAR = True) - only
# rendered while hp < max_hp, red fill per the design ask.
ENEMY_HEALTH_BAR_WIDTH = 24
ENEMY_HEALTH_BAR_HEIGHT = 3
ENEMY_HEALTH_BAR_OFFSET_Y = 4
ENEMY_HEALTH_BAR_BG_COLOR = (40, 40, 40, 220)
ENEMY_HEALTH_BAR_FILL_COLOR = (200, 40, 40)
ENEMY_HEALTH_BAR_BORDER_COLOR = (10, 10, 10)

# src.entities.DamageNumber - floating combat-text color for damage taken.
DAMAGE_NUMBER_COLOR = pygame.Color(190, 80, 230)

# Debug overlay (src/debug.py, drawn from src.map.Level.render) - translucent
# hurtbox/hitbox rectangles for tuning collision/attack-range sizes visually.
# Just the default at startup - press 'h' in-game to toggle (src.Game.on_input).
DEBUG_HITBOXES = False
DEBUG_HURTBOX_COLOR = (160, 60, 220, 90)  # translucent purple - entity hurtboxes
DEBUG_HITBOX_COLOR = (220, 40, 40, 90)  # translucent red - attack hit areas

# Used by src.entities.Player / src.ui.HUD. No leveling curve yet - flat
# XP-to-next-level constant until that's designed.
PLAYER_MAX_HP = 100
PLAYER_XP_TO_NEXT_LEVEL = 100

# Register your tilemaps from the maps folder, for instance:
# TILEMAPS = {
#     'zone_1': str(BASE_DIR / "assets" / "maps" / "zone_1.json")
# }
TILEMAPS = {
    "forest": str(BASE_DIR / "assets" / "maps" / "forest.json"),
}

# Register your textures from the graphics folder, for instance:
# TEXTURES = {
#     'my_texture': pygame.image.load(BASE_DIR / "assets" / "graphics" / "my_texture.png")
# }
TEXTURES = {
    # 160x96 - 5x3 grid of 32x32 cells, matching src.entities.Player's
    # 32x32 collision box. Row-major frame indices: idle 0-3 (rest of row
    # 0 unused), run 5-7 (rest of row 1 unused), dash 10-14.
    "marze": pygame.image.load(BASE_DIR / "assets" / "graphics" / "Marze.png"),
    "small_demon": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "small-demon.png"
    ),
    # 128x32 - 4 distinct 32x32 ability icons, in HUD slot order.
    "marze_abilities": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "marze-abilities.png"
    ),
}

# Register your frames, for instance:
# FRAMES = {
#     'my_frames': frames.generate_frames(TEXTURES['my_texture'], 16, 16)
# }
FRAMES = {
    "marze": frames.generate_frames(TEXTURES["marze"], 32, 32),
    # 800x600, 8 cols x 6 rows of 100x100 cells. Row-major frame indices:
    # idle 0-5, run 8-15, (unused) 16-22, attack 24-30, hurt 32-35, dead 40-43.
    "small_demon": frames.generate_frames(TEXTURES["small_demon"], 100, 100),
    "marze_abilities": frames.generate_frames(TEXTURES["marze_abilities"], 32, 32),
}

# Register your sound from the sounds folder, for instance:
# SOUNDS = {
#     'my_sound': pygame.mixer.Sound(BASE_DIR / "assets"  / "sounds" / "my_sound.wav"),
# }
SOUNDS = {}

# Register your fonts from the fonts folder, for instance:
# FONTS = {
#     'small': pygame.font.Font(BASE_DIR / "assets"  / "fonts" / "font.ttf", 8)
# }
FONTS = {}
