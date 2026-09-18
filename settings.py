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
# Climbing vines (src.entities.player_states.ClimbState) - only takes
# effect while touching a "vines" tile whose collision property is
# "climbable".
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_UP, "move_up")
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_DOWN, "move_down")
input_handler.InputHandler.set_keyboard_action(
    input_handler.KEY_h, "toggle_debug_hitboxes"
)
# Chest purchase (src.entities.Chest) - press near a closed chest to buy.
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_f, "interact")
# Reset-the-level choice at an altar once its buff has ended
# (src.entities.Altar, src.states.PlayState._reset_level).
input_handler.InputHandler.set_keyboard_action(input_handler.KEY_g, "reset")

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

# Vertical speed while climbing a "vines" tile (src.entities.
# player_states.ClimbState) - gravity is cancelled entirely while
# climbing, so this is the player's only vertical speed there.
CLIMB_SPEED = 60

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
PLAYER_RAGE_DURATION = 1.0
PLAYER_RAGE_RADIUS = 64
PLAYER_RAGE_HITS = 4
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

# Used by src.entities.enemy_states.FollowState/AttackState - close to
# the player's own PLAYER_SPEED so a chase is genuinely threatening
# rather than something you can just outwalk.
DEMON_SPEED = round(PLAYER_SPEED * 0.95)
DEMON_ATTACK_RANGE = 24
# How long the demon stands idle after its attack animation finishes before
# resuming the chase - on top of the attack animation's own runtime.
DEMON_ATTACK_COOLDOWN = 0.6
# Base attack damage/max_hp before the current difficulty tier's
# enemy_damage_multiplier/enemy_hp_multiplier scale a newly spawned
# SmallDemon (see DIFFICULTY_TIERS below and SmallDemon.__init__).
DEMON_ATTACK_DAMAGE = 10
DEMON_MAX_HP = 40

# Periodic random spawning - src.states.PlayState._spawn_demon. One demon
# spawns on solid ground somewhere between MIN and MAX tile columns away
# from the player (randomly to either side) every spawn_interval seconds
# - no cap on how many can be active at once - driven by the current
# difficulty tier (see DIFFICULTY_TIERS below) rather than a flat constant.
DEMON_SPAWN_MIN_DISTANCE_TILES = 4
DEMON_SPAWN_MAX_DISTANCE_TILES = 10

# Demon vine-climbing (src.entities.enemy_states.FollowState/ClimbState) -
# reuses CLIMB_SPEED/JUMP_TAKEOFF_SPEED already tuned for the player. A
# demon touching a climbable tile only grabs on while its target is more
# than this many pixels above/below it, and climbing stops once it's
# back within this same distance - so it doesn't hunt for exact pixel
# alignment before resuming the horizontal chase.
DEMON_CLIMB_ALIGN_THRESHOLD = 8

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
DODGE_TEXT_COLOR = pygame.Color(255, 255, 255)  # "Dodged!" popup color

# Debug overlay (src/debug.py, drawn from src.map.Level.render) - translucent
# hurtbox/hitbox rectangles for tuning collision/attack-range sizes visually.
# Just the default at startup - press 'h' in-game to toggle (src.Game.on_input).
DEBUG_HITBOXES = False
DEBUG_HURTBOX_COLOR = (160, 60, 220, 90)  # translucent purple - entity hurtboxes
DEBUG_HITBOX_COLOR = (220, 40, 40, 90)  # translucent red - attack hit areas

# Used by src.entities.Player / src.ui.HUD.
PLAYER_MAX_HP = 100
PLAYER_XP_TO_NEXT_LEVEL = 100
# Each level-up multiplies the next level's XP requirement by this, so
# leveling gets progressively harder - see Player.grant_xp.
PLAYER_LEVEL_XP_MULTIPLIER = 1.5
# Flat base-stat growth applied by Player.grant_xp on every level-up.
# Current hp is not topped up - only the max_hp ceiling rises.
PLAYER_LEVEL_UP_HP_BONUS = 10
PLAYER_LEVEL_UP_DAMAGE_BONUS = 2

# Base gold/XP granted per demon kill (src.entities.SmallDemon.take_damage),
# scaled by the current difficulty tier's reward_multiplier (see
# DIFFICULTY_TIERS below).
DEMON_BASE_GOLD_REWARD = 5
DEMON_BASE_XP_REWARD = 10

# Named difficulty tiers (src.states.PlayState.update picks the last tier
# whose start_time <= elapsed play time, and holds there once past the
# final tier's start_time) - src.ui.HUD displays the current tier's name
# (and tints it plus the run timer's fill bar with "color") next to the
# run timer sign. Each tier's spawn_interval replaces settings.
# DEMON_SPAWN_INTERVAL for PlayState._spawn_demon (no cap on how many
# demons can be active at once), and enemy_hp_multiplier/
# enemy_damage_multiplier scale a newly spawned SmallDemon's max_hp/
# attack_damage - existing demons don't retroactively get stronger when
# a tier changes. "color" ramps calm green -> yellow -> orange -> intense
# red, reading progressively scarier as it climbs.
DIFFICULTY_TIERS = [
    {
        "name": "Easy",
        "start_time": 0.0,
        "reward_multiplier": 1.0,
        "enemy_hp_multiplier": 1.0,
        "enemy_damage_multiplier": 1.0,
        "spawn_interval": 4.0,
        "color": pygame.Color(90, 200, 90),
    },
    {
        "name": "Medium",
        "start_time": 180.0,
        "reward_multiplier": 1.3,
        "enemy_hp_multiplier": 1.3,
        "enemy_damage_multiplier": 1.2,
        "spawn_interval": 3.0,
        "color": pygame.Color(230, 200, 90),
    },
    {
        "name": "Hard",
        "start_time": 360.0,
        "reward_multiplier": 1.6,
        "enemy_hp_multiplier": 1.6,
        "enemy_damage_multiplier": 1.4,
        "spawn_interval": 2.5,
        "color": pygame.Color(230, 130, 40),
    },
    {
        "name": "Very Hard",
        "start_time": 600.0,
        "reward_multiplier": 2.0,
        "enemy_hp_multiplier": 2.0,
        "enemy_damage_multiplier": 1.6,
        "spawn_interval": 2.0,
        "color": pygame.Color(220, 30, 30),
    },
]

# Run timer sign (src.ui.HUD, assets/graphics/sign-timer.png) - the bar
# fills once over this many seconds of elapsed play time and stays full
# after, a one-shot overall run-progress indicator (separate from the
# repeating DIFFICULTY_* cycle above).
RUN_TIMER_MAX_DURATION_SECONDS = 1200.0  # 20 minutes
# sign-timer.png is 32x64 - this inset rect (in the sprite's own pixel
# space) is where the fill bar draws, centered within the post (itself a
# 6px-wide, 38px-tall stem below the hook-shaped cap, tapering to a point
# at the very bottom) but narrower than it so wood shows on either side.
RUN_TIMER_BAR_RECT = pygame.Rect(23, 20, 2, 38)
# The sign's flat brown board area above the bar (same sprite-space as
# RUN_TIMER_BAR_RECT above) - where the mm:ss readout is centered.
RUN_TIMER_LABEL_RECT = pygame.Rect(4, 8, 22, 8)
RUN_TIMER_SCALE = 2
# The bar fill and tier-name text are tinted by the current tier's own
# "color" (DIFFICULTY_TIERS above) instead of a fixed color - only the
# mm:ss readout stays neutral.
RUN_TIMER_TEXT_COLOR = pygame.Color(255, 255, 255)

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
ITEM_CRIT_CHANCE_BONUS = 0.05  # Hunter's hat - crit chance, per stack
ITEM_CRIT_DAMAGE_MULTIPLIER = 2.0  # Hunter's hat - damage multiplier on a crit
ITEM_DODGE_CHANCE_BONUS = 0.05  # Cat's spirit - dodge chance, per stack
ITEM_DODGE_CHANCE_CAP = 0.75  # Cap so cat's spirit stacks can't reach 100% dodge
ITEM_COOLDOWN_REDUCTION_FACTOR = 0.9  # Loadstone - cooldown multiplier, per stack
ITEM_COOLDOWN_REDUCTION_FLOOR = (
    0.2  # Floor so loadstone stacks can't zero out cooldowns
)
ITEM_BLOOD_THIRST_COOLDOWN_REDUCTION = (
    0.25  # Blood thirst - flat cooldown timer cut, per stack, per landed crit
)
ITEM_SAMURAI_PROC_CHANCE = 0.05  # Samurai sword - chance of a rage-style AOE burst on any landed hit, per stack
ITEM_SAMURAI_PROC_CHANCE_CAP = (
    0.5  # Cap so samurai sword stacks can't make every hit burst
)
ITEM_JIMBO_DAMAGE_MULTIPLIER = (
    4.0  # Jimbo - flat damage multiplier while owned (does not stack further)
)
ITEM_SOUL_BOX_BONUS_PER_KILL = (
    1  # Soul box - flat base damage gained per kill, per stack
)

# Pickup idle bob (src.items.Pickup) - same sine-tween trick as
# ThrownSword's floating swords, just its own constants since the icons
# are half the size (16x16 vs 32x32) and may want independent tuning.
ITEM_FLOAT_AMPLITUDE = 3
ITEM_FLOAT_SPEED = 4.5

# Pickup outline glow color (src.items.Pickup.render), keyed by texture
# id - white for the common items, red for the rarer red-items.png set.
ITEM_OUTLINE_COLORS = {
    "items": pygame.Color(255, 255, 255),
    "red_items": pygame.Color(220, 30, 30),
}

# Parallax background (src.map.Background.ParallaxBackground) - each
# scrolling layer's factor is the fraction of the camera's own horizontal
# movement it scrolls by (0 = fixed in place, 1 = moves exactly with the
# world/tilemap), back to front: the wide forest silhouette barely
# scrolls, huge-trees a bit more, tall-trees' bare-branch row (its
# farther row) more still, tall-trees' leafy row (its closer row) the
# most. huge-trees.png/tall-trees.png's cells are rescaled to a HEIGHT
# (px, aspect-preserved) and pinned to the top of the screen (an
# overhead canopy, unlike the bottom-anchored forest silhouette) before
# being scattered at SPACING intervals (+/- JITTER, in pixels) along the
# layer, each instance randomly picking one of its layer's frame
# variants - computed once per Level (Level.__init__ builds one
# ParallaxBackground) rather than tiled, since these sheets are already
# wider than this map's own scroll range.
BACKGROUND_FOREST_SCROLL_FACTOR = 0.1
# background-forest.png is a single wide 1440x800 silhouette, drastically
# taller than the 360px-tall viewport - left at native size (and bottom-
# anchored), its solid ground fill alone was tall enough to cover the
# entire screen, hiding the treeline silhouette above it entirely. Scaled
# down (aspect-preserved) so its own top edge - not a fixed row within
# the art - lands at BACKGROUND_FOREST_TOP_RATIO of the screen height,
# same bottom-anchoring as before.
BACKGROUND_FOREST_TOP_RATIO = 0.01
BACKGROUND_FOREST_HEIGHT = round(VIRTUAL_HEIGHT * (1 - BACKGROUND_FOREST_TOP_RATIO))
BACKGROUND_HUGE_TREES_SCROLL_FACTOR = 0.3
BACKGROUND_HUGE_TREES_HEIGHT = 300
BACKGROUND_HUGE_TREES_SPACING = 260
BACKGROUND_HUGE_TREES_JITTER = 40
# tall-trees.png's bare-branch row (src.map.Background's
# _TALL_TREES_BACK_ROW_INDICES) - the farther of its two rows.
BACKGROUND_TALL_TREES_BACK_SCROLL_FACTOR = 0.4
BACKGROUND_TALL_TREES_BACK_HEIGHT = 330
BACKGROUND_TALL_TREES_BACK_SPACING = 220
BACKGROUND_TALL_TREES_BACK_JITTER = 30
# tall-trees.png's leafy row (_TALL_TREES_FRONT_ROW_INDICES) - the
# nearer of its two rows, and the frontmost background layer overall.
BACKGROUND_TALL_TREES_SCROLL_FACTOR = 0.5
BACKGROUND_TALL_TREES_HEIGHT = 360
BACKGROUND_TALL_TREES_SPACING = 200
BACKGROUND_TALL_TREES_JITTER = 30

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
    # 128x16 - 8 distinct 16x16 item icons (stat-boosting pickups,
    # src.items.Pickup), rendered as white silhouettes, each with a white
    # outline baked into the art. Frame indices 0-7, in
    # src.items.definitions.ITEMS order: cane, heart, knife, shield,
    # daggers, hunter's hat, cat's spirit, loadstone.
    "items": pygame.image.load(BASE_DIR / "assets" / "graphics" / "white-items.png"),
    # 64x16 - 4 distinct 16x16 item icons, same white-silhouette-with-
    # outline treatment as "items" but the rarer/stronger pickups. Frame
    # indices 0-3, in src.items.definitions.ITEMS order: blood thirst,
    # samurai sword, jimbo, soul box.
    "red_items": pygame.image.load(BASE_DIR / "assets" / "graphics" / "red-items.png"),
    # Parallax background layers (src.map.Background.ParallaxBackground),
    # back to front. background-forest.png (1440x800) is a single wide
    # treeline silhouette, blitted whole. huge-trees.png (2400x1000, 3x2
    # grid of 800x500 cells) and tall-trees.png (1200x1248, 2x2 grid of
    # 600x624 cells) are each scattered as individual tree instances -
    # see FRAMES below for their cell slicing.
    "background_forest": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "background-forest.png"
    ),
    "huge_trees": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "huge-trees.png"
    ),
    "tall_trees": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "tall-trees.png"
    ),
    # 160x192 - 4x4 grid of 40x48 cells, 4 separate slash animations
    # (src.entities.HitEffect). Only the first row (frame indices 0-3) is
    # used, played over an enemy hit by the rage/samurai sword AOE
    # bursts; the other three rows are unused for now.
    "blade_effects": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "blade-effects.png"
    ),
    # 128x32 - 4 32x32 coin-spin frames, looped by src.ui.HUD next to the
    # gold counter.
    "gold_icon": pygame.image.load(BASE_DIR / "assets" / "graphics" / "gold-icon.png"),
    # 32x64 - a single signpost sprite (not a frame sheet), drawn scaled
    # up by RUN_TIMER_SCALE in src.ui.HUD's top-right run timer.
    "sign_timer": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "sign-timer.png"
    ),
    # 96x16 - six 16x16 frames (src.entities.Chest): frame 0 closed, the
    # remaining 5 the opening animation, ending on the fully-open frame.
    "chest": pygame.image.load(BASE_DIR / "assets" / "graphics" / "chest.png"),
    # 320x80 - four 80x80 frames (src.entities.Altar): frame 0 dormant,
    # the remaining 3 the activation animation, ending on the active frame.
    "altars": pygame.image.load(BASE_DIR / "assets" / "graphics" / "altars.png"),
    # 64x144 - four 16x144 pillar column frames (src.entities.Decoration,
    # flanking the player's spawn point - see
    # src.states.PlayState._spawn_pillars). Only frame 0 is used today.
    "ruins_pillars": pygame.image.load(
        BASE_DIR / "assets" / "graphics" / "ruins-pillars.png"
    ),
}

# The single pixel in background.png is the parallax background's sky
# fill color (src.map.Background.ParallaxBackground) - sampled once here
# rather than registered as a texture, since it's never blitted as an
# image.
BACKGROUND_SKY_COLOR = pygame.image.load(
    BASE_DIR / "assets" / "graphics" / "background.png"
).get_at((0, 0))

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
    "items": frames.generate_frames(TEXTURES["items"], 16, 16),
    "red_items": frames.generate_frames(TEXTURES["red_items"], 16, 16),
    "huge_trees": frames.generate_frames(TEXTURES["huge_trees"], 800, 500),
    "tall_trees": frames.generate_frames(TEXTURES["tall_trees"], 600, 624),
    "blade_effects": frames.generate_frames(TEXTURES["blade_effects"], 40, 48),
    "gold_icon": frames.generate_frames(TEXTURES["gold_icon"], 32, 32),
    "chest": frames.generate_frames(TEXTURES["chest"], 16, 16),
    "altars": frames.generate_frames(TEXTURES["altars"], 80, 80),
    "ruins_pillars": frames.generate_frames(TEXTURES["ruins_pillars"], 16, 144),
}

# src.ui.HUD - seconds each gold_icon coin-spin frame holds for.
GOLD_ICON_FRAME_INTERVAL = 0.15

# Chests (src.entities.Chest, assets/graphics/chest.png) - spawned by
# PlayState.enter from the map's "chests" object layer (a set of possible
# spawn points; not every point gets a chest each run). Costs gold to
# open (press "interact" while touching one), scaled by the current
# difficulty tier's reward_multiplier so chests get pricier alongside
# richer kill rewards. A 90/10 roll picks a random item from ITEMS'
# "items" (white) vs "red_items" (rare) pool as the payout.
CHEST_BASE_COST = 20
CHEST_SPAWN_MIN = 6
CHEST_SPAWN_MAX = 8
CHEST_RED_ITEM_CHANCE = 0.10
# 5 opening frames (indices 1-5) played at this interval before settling
# on the last one permanently.
CHEST_OPEN_FRAME_INTERVAL = 0.08
# How long after the lid finishes opening before the rolled item actually
# spawns as a Pickup - lets the player run off and keep playing, then
# decide later whether it's worth coming back for, instead of it
# appearing (and likely auto-collecting) the instant the chest opens.
CHEST_ITEM_REVEAL_DELAY = 0.3

# Altar (src.entities.Altar, assets/graphics/altars.png) - one spawns per
# map, at a random point from the map's "altars" object layer (a set of
# possible spawn points, just like chests). Free to activate (press
# "interact" while touching it, no gold cost) - one-time only, then plays
# its 3-frame activation animation and stays on the final frame
# permanently. Activating starts a run-wide ALTAR_BUFF_DURATION-second
# buff (src.states.PlayState) that multiplies the current difficulty
# tier's spawn_interval by ALTAR_SPAWN_INTERVAL_MULTIPLIER (monsters show
# up roughly twice as often), with the remaining seconds displayed above
# the player's head the whole time.
ALTAR_BUFF_DURATION = 90.0
ALTAR_SPAWN_INTERVAL_MULTIPLIER = 0.5
# 3 activation frames (indices 1-3) played at this interval before
# settling on the last one permanently.
ALTAR_ACTIVATE_FRAME_INTERVAL = 0.15

# Player spawn point (src.states.PlayState._spawn_player/_spawn_pillars)
# - picked once per level from the map's "spawns" object layer (a set of
# possible spawn points, same pattern as chests/altars), then flanked by
# two ruins-pillars.png decorations this many pixels out from the
# point's own center on either side.
PILLAR_SPAWN_GAP = 20

# src.entities.HitEffect - seconds each of its 4 frames holds for (a
# quick flash - the whole animation plays out in 4x this, well under the
# rage/samurai burst's own timing).
HIT_EFFECT_FRAME_INTERVAL = 0.05

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
