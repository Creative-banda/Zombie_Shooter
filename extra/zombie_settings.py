import pygame
from pathlib import Path
import os

pygame.init()
pygame.mixer.init()

# Virtual Resolution (Logical Resolution for Game Logic)
VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 600

# Get Actual Screen Resolution
try:
    actual_screen_width, actual_screen_height = pygame.display.get_desktop_sizes()[0]
except:
    actual_screen_width, actual_screen_height = 800, 600

# Use desktop resolution or fallback to 800x600 if not available

# Set display mode early to allow .convert() and .convert_alpha()
screen = pygame.display.set_mode((actual_screen_width, actual_screen_height))

# Scaling Factors
scale_x = actual_screen_width / VIRTUAL_WIDTH
scale_y = actual_screen_height / VIRTUAL_HEIGHT

CELL_SIZE_SCALED = int(45 * scale_x)
COLLECT_ITEM_SIZE_SCALED = int(20 * scale_x)

# General Settings
FPS = 500
BASE_FPS = 70

MAX_LEVEL = 3  # Maximum number of levels in the game

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)

# Sizes
PLAYER_SIZE = int(30 * scale_x) 
BULLET_SIZE = int(2 * scale_x)
BULLET_SPEED = int(7 * scale_x)
ZOMBIE_SIZE = int(35 * scale_x)
ZOMBIE_SPEED = int(1 * scale_x)

TORCH_RADIUS = int(180 * scale_x)

PLAYER_SPEED = int(2*scale_x)

# Get the script's directory
current_path = Path(__file__).parent

# Move up one level to remove "extra"
parent_path = current_path.parent

# Correct ASSETS_DIR
ASSETS_DIR = parent_path / "zombie_assets"

IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sound_effect"
LEVELS_DIR = ASSETS_DIR / "levels"

# Helper to load and convert images
def load_image(path, scale=None, alpha=True):
    img = pygame.image.load(path)
    if alpha:
        img = img.convert_alpha()
    else:
        img = img.convert()
    if scale:
        img = pygame.transform.scale(img, scale)
    return img

# Asset Files
bullet_image = load_image(IMAGES_DIR / "bullet.png")
health_image = load_image(IMAGES_DIR / "health.png")
akm_image = load_image(IMAGES_DIR / "AKM.png")
rifle_ammo_image = load_image(IMAGES_DIR / "rifle_ammo.png")
shotgun_image = load_image(IMAGES_DIR / "shotgun.png")
shotgun_ammo_image = load_image(IMAGES_DIR / "shotgun_bullet.png")
piston_ammo_image = load_image(IMAGES_DIR / "piston_bullet.png")
bg_image = load_image(IMAGES_DIR / "background.jpg", alpha=False) # Background usually doesn't need alpha
wall_image = load_image(IMAGES_DIR / "wall.PNG")
breakable_wall_image = load_image(IMAGES_DIR / "break_wall.png")
dead_zombie_image = load_image(IMAGES_DIR / "dead_zombie.png", scale=(ZOMBIE_SIZE, ZOMBIE_SIZE))

# Pre-load sounds
def load_sound(path):
    return pygame.mixer.Sound(str(path))

SOUND_EFFECTS = {
    "gun_pickup": load_sound(SOUNDS_DIR / "gun_pickup.mp3"),
    "item_pickup": load_sound(SOUNDS_DIR / "collect_item.mp3"),
    "death": load_sound(SOUNDS_DIR / "death.mp3"),
    "victory": load_sound(SOUNDS_DIR / "victory_sound.mp3"),
    "loose": load_sound(SOUNDS_DIR / "loose.mp3"),
    "walk": load_sound(SOUNDS_DIR / 'player_walk.mp3'),
    "empty_gun": load_sound(SOUNDS_DIR / 'gun_sound/empty_gun.mp3'),
    "zombie_see": load_sound(SOUNDS_DIR / 'zombie_see_1.mp3'),
    "alert": load_sound(SOUNDS_DIR / 'alert.mp3'),
}

# Pre-load random sounds
SOUND_EFFECTS["damage"] = [load_sound(SOUNDS_DIR / f"damage_sound/{i}.mp3") for i in range(1, 6)]
SOUND_EFFECTS["zombie_die"] = [load_sound(SOUNDS_DIR / f"zombie_die/zombie_die{i}.mp3") for i in range(1, 4)]

# Legacy compatibility
gun_pickup_sound = SOUND_EFFECTS["gun_pickup"]
item_pickup_sound = SOUND_EFFECTS["item_pickup"]
death_sound = SOUND_EFFECTS["death"]
victory_sound = SOUND_EFFECTS["victory"]
loose_sound = SOUND_EFFECTS["loose"]
walk_sound = SOUND_EFFECTS["walk"]
background_music = load_sound(SOUNDS_DIR / 'background_music.mp3')

# Player Gun Info
gun_info = {
    "handgun": {
        "damage": 20, "ammo": 15,
        "magazine": 6, "cooldown": 0,
        "remaining_ammo": 6, "sound": load_sound(SOUNDS_DIR / 'gun_sound/handgun.mp3'),
        "reloading_sound" : load_sound(SOUNDS_DIR / 'gun_sound/handgun_reload.mp3')
    },
    "rifle": {
        "damage": 50, "ammo": 40,
        "magazine": 20, "cooldown": 100,
        "remaining_ammo": 20, "sound": load_sound(SOUNDS_DIR / 'gun_sound/rifle.mp3'),
        "reloading_sound" : load_sound(SOUNDS_DIR / 'gun_sound/rifle_reload.mp3')
    },
    "shotgun": {
        "damage": 100, "ammo": 10,
        "magazine": 2, "cooldown": 1000,
        "remaining_ammo": 2, "sound": load_sound(SOUNDS_DIR / 'gun_sound/shotgun_shot.mp3'),
        "reloading_sound" : load_sound(SOUNDS_DIR / 'gun_sound/shotgun_reload.mp3')
    }
}

# Pre-load Animations
def load_animations(base_path, types, size, rotations):
    anim_dict = {}
    for i, t in enumerate(types):
        anim_dict[i] = []
        path = base_path / t
        if not path.exists():
            continue
        # Use sorted listdir to maintain frame order
        frames = sorted([f for f in os.listdir(path) if f.endswith('.png')], key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else x)
        for frame in frames:
            img = load_image(path / frame, scale=size)
            rotated = {}
            for name, angle in rotations.items():
                if angle == 0:
                    rotated[name] = img
                else:
                    rotated[name] = pygame.transform.rotate(img, angle)
            anim_dict[i].append(rotated)
    return anim_dict

PLAYER_ROTATIONS = {"up": 90, "down": 270, "left": 180, "right": 0}
ZOMBIE_ROTATIONS = {"up": 0, "right": 270, "down": 180, "left": 90}

PLAYER_ANIMATIONS = {}
for gun in ["handgun", "rifle", "shotgun"]:
    PLAYER_ANIMATIONS[gun] = load_animations(IMAGES_DIR / "player" / gun, ["idle", "move", "reload", "shoot"], (PLAYER_SIZE, PLAYER_SIZE), PLAYER_ROTATIONS)

# Zombie Animations
# Zombie frames are named skeleton-move_0.png, etc. Need a slightly different loader for them.
def load_zombie_animations(base_path, types, size, rotations):
    anim_dict = {}
    for i, t in enumerate(types):
        anim_dict[i] = []
        path = base_path / t
        if not path.exists():
            continue
        # Frames are skeleton-move_0.png
        frames = sorted([f for f in os.listdir(path) if f.endswith('.png')], key=lambda x: int(x.split('_')[-1].split('.')[0]))
        for frame in frames:
            img = load_image(path / frame, scale=size)
            rotated = {}
            for name, angle in rotations.items():
                if angle == 0:
                    rotated[name] = img
                else:
                    rotated[name] = pygame.transform.rotate(img, angle)
            anim_dict[i].append(rotated)
    return anim_dict

ZOMBIE_ANIMATIONS = load_zombie_animations(IMAGES_DIR / "zombie", ["move", "idle", "attack"], (ZOMBIE_SIZE, ZOMBIE_SIZE), ZOMBIE_ROTATIONS)
