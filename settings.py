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

input_handler.InputHandler.set_keyboard_action(input_handler.KEY_ESCAPE, 'quit')
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_RIGHT, 'move_right')
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_d, 'move_right')
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_LEFT, 'move_left')
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_a, 'move_left')
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_SPACE, 'jump')

TITLE = 'Dungeon Prob'

# Size we want to emulate
VIRTUAL_WIDTH = 320
VIRTUAL_HEIGHT = 180

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

# Register your tilemaps from the maps folder, for instance:
# TILEMAPS = {
#     'zone_1': str(BASE_DIR / "assets" / "maps" / "zone_1.json")
# }
TILEMAPS = {
    'forest': str(BASE_DIR / "assets" / "maps" / "forest.json"),
}

# Register your textures from the graphics folder, for instance:
# TEXTURES = {
#     'my_texture': pygame.image.load(BASE_DIR / "assets" / "graphics" / "my_texture.png")
# }
TEXTURES = {
    'marze': pygame.image.load(BASE_DIR / "assets" / "graphics" / "Marze.png"),
}

# Register your frames, for instance:
# FRAMES = {
#     'my_frames': frames.generate_frames(TEXTURES['my_texture'], 16, 16)
# }
FRAMES = {
    # Marze.png is a single 16x16 sprite by now - one frame, no animation yet.
    'marze': frames.generate_frames(TEXTURES['marze'], 16, 16),
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
