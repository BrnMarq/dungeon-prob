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

# Fixed-height jump - always the same takeoff speed regardless of how long
# "jump" is held (see src.entities.player_states.PlayingState).
JUMP_TAKEOFF_SPEED = GRAVITY / 4

# Dash: a short, gravity-cancelling horizontal burst - see
# src.entities.player_states.DashState. Duration matches the 7-frame dash
# animation (Marze.png row 2) so the streak frames play out over the burst.
PLAYER_DASH_SPEED = 320
PLAYER_DASH_DURATION = 0.25
PLAYER_DASH_COOLDOWN = 3
# Outlasts the dash itself - invincibility covers the recovery window right
# after the burst too, not just the movement.
PLAYER_INVINCIBILITY_DURATION = 1.0

# Front-facing melee attack (Q ability) - src.entities.player_states.AttackState.
# No dedicated sprite yet, so it plays the idle animation for its duration
# instead - see AttackState for the hit-frame timing this implies.
PLAYER_ATTACK_RANGE = 20
# How far the hitbox's near edge sits inside Marze's own hurtbox rather
# than starting flush at it - the swing visually originates from the
# body, not a hard edge, without going back to covering the whole hurtbox.
PLAYER_ATTACK_INSET = 6
PLAYER_ATTACK_DAMAGE = 15
PLAYER_ATTACK_DURATION = 0.3

# Thrown sword (W ability) - src.entities.player_states.ThrowState plays
# Marze.png's 3-frame throw wind-up, then hands off to src.entities.
# ThrownSword for the projectile itself (assets/graphics/dark-sword.png).
PLAYER_THROW_DAMAGE = 15
PLAYER_THROW_DURATION = 0.3
PLAYER_THROW_COOLDOWN = 4

# Invincible radius burst (R ability) - src.entities.player_states.RageState
# plays Marze.png's row-5 3-frame wind-up (frames 25-27), holds on the last
# frame for the bulk of the duration, then plays it backward as the ability
# ends. Hits everything within PLAYER_RAGE_RADIUS of the player's center
# PLAYER_RAGE_HITS times, evenly spaced across PLAYER_RAGE_DURATION.
PLAYER_RAGE_DURATION = 2.0
PLAYER_RAGE_RADIUS = 64
PLAYER_RAGE_HITS = 8
PLAYER_RAGE_HIT_INTERVAL = PLAYER_RAGE_DURATION / PLAYER_RAGE_HITS
PLAYER_RAGE_DAMAGE = 10
PLAYER_RAGE_COOLDOWN = 8
# Each direction (wind-up, wind-down) of the 3-frame row-5 animation plays
# over this many seconds per frame - independent of PLAYER_RAGE_DURATION so
# it reads as a quick flourish rather than stretching across the whole burst.
PLAYER_RAGE_ANIM_FRAME_INTERVAL = 0.1

# ThrownSword's flight: same speed/duration as the dash, so it travels the
# same distance in the same time (PLAYER_DASH_SPEED * PLAYER_DASH_DURATION).
SWORD_SPEED = PLAYER_DASH_SPEED
SWORD_TRAVEL_DISTANCE = SWORD_SPEED * PLAYER_DASH_DURATION
# Fraction of SWORD_TRAVEL_DISTANCE covered by each of dark-sword.png's
# flight animations, in order - thrown/midair/near_max_travel - the
# remainder (up to 1.0) is near_max_travel's share.
SWORD_THROWN_DISTANCE_FRACTION = 0.2
SWORD_MIDAIR_DISTANCE_FRACTION = 0.7
# Frame intervals derived so each flight animation plays out exactly over
# the portion of PLAYER_DASH_DURATION its distance fraction takes at
# SWORD_SPEED - same trick as PLAYER_DASH_DURATION / 5 for the dash streak.
SWORD_THROWN_FRAME_INTERVAL = PLAYER_DASH_DURATION * SWORD_THROWN_DISTANCE_FRACTION / 3
SWORD_MIDAIR_FRAME_INTERVAL = (
    PLAYER_DASH_DURATION
    * (SWORD_MIDAIR_DISTANCE_FRACTION - SWORD_THROWN_DISTANCE_FRACTION)
    / 2
)
SWORD_NEAR_MAX_FRAME_INTERVAL = (
    PLAYER_DASH_DURATION * (1 - SWORD_MIDAIR_DISTANCE_FRACTION) / 4
)

# Once landed, ThrownSword loops its 3 floating frames and tweens its y
# position with a sine wave - amplitude in pixels, speed in radians/second.
SWORD_FLOAT_FRAME_INTERVAL = 0.15
SWORD_FLOAT_AMPLITUDE = 4
SWORD_FLOAT_SPEED = 3.0

# Touching a floating sword detonates it - gale.particle_system burst plus
# area damage, and refunds the player's dash (see ThrownSword._explode).
SWORD_EXPLOSION_RADIUS = 48
SWORD_EXPLOSION_DAMAGE = 20
SWORD_EXPLOSION_PARTICLE_COUNT = 24
SWORD_EXPLOSION_COLOR = pygame.Color(20, 20, 20, 255)

# Used by src.entities.enemy_states.FollowState/AttackState.
DEMON_SPEED = 40
DEMON_ATTACK_RANGE = 24
# How long the demon stands idle after its attack animation finishes before
# resuming the chase - on top of the attack animation's own runtime.
DEMON_ATTACK_COOLDOWN = 0.6
DEMON_ATTACK_DAMAGE = 10
DEMON_MAX_HP = 40

# Periodic random spawning - src.states.PlayState._spawn_demon. Every
# DEMON_SPAWN_INTERVAL seconds, one demon spawns on solid ground somewhere
# between MIN and MAX tile columns away from the player (randomly to
# either side), as long as fewer than DEMON_MAX_ACTIVE are already alive.
DEMON_SPAWN_INTERVAL = 4.0
DEMON_SPAWN_MIN_DISTANCE_TILES = 4
DEMON_SPAWN_MAX_DISTANCE_TILES = 10
DEMON_MAX_ACTIVE = 5

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
    # 250x240 - 5x6 grid of 50x40 cells, padded larger than
    # src.entities.Player's 32x32 collision box to give the attack swing
    # room to animate (Player.sprite_offset re-centers it on the hitbox).
    # Row-major frame indices: idle 0-3 (rest of row 0 unused), run 5-7
    # (rest of row 1 unused), dash 10-14, attack 15-17 (rest of row 3
    # unused), throw 20-22 (W ability wind-up, rest of row 4 unused), rage
    # 25-27 (R ability wind-up/wind-down, rest of row 5 unused).
    "marze": pygame.image.load(BASE_DIR / "assets" / "graphics" / "Marze.png"),
    "small_demon": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "small-demon.png"
    ),
    # 128x32 - 4 distinct 32x32 ability icons, in HUD slot order.
    "marze_abilities": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "marze-abilities.png"
    ),
    # 128x128 - 4x4 grid of 32x32 cells, the W ability's projectile
    # (src.entities.ThrownSword). Row-major frame indices: thrown 0-2,
    # midair 4-5, near_max_travel 8-11, floating 12-14 (unused cells on
    # each row's tail are blank).
    "dark_sword": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "dark-sword.png"
    ),
}

# Register your frames, for instance:
# FRAMES = {
#     'my_frames': frames.generate_frames(TEXTURES['my_texture'], 16, 16)
# }
FRAMES = {
    "marze": frames.generate_frames(TEXTURES["marze"], 50, 40),
    # 800x700, 8 cols x 7 rows of 100x100 cells. Row-major frame indices:
    # idle 0-5, run 8-15, (unused) 16-22, attack 24-30, hurt 32-35,
    # dead 40-43, spawn 48-51.
    "small_demon": frames.generate_frames(TEXTURES["small_demon"], 100, 100),
    "marze_abilities": frames.generate_frames(TEXTURES["marze_abilities"], 32, 32),
    "dark_sword": frames.generate_frames(TEXTURES["dark_sword"], 32, 32),
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
