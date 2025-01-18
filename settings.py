import pygame
import pathlib


pygame.display.init()
pygame.mixer.init()


# Virtual Resolution (Logical Resolution for Game Logic)
VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 600

# Get Actual Screen Resolution
actual_screen_width, actual_screen_height = pygame.display.get_desktop_sizes()[0]

# Scaling Factors
scale_x = actual_screen_width / VIRTUAL_WIDTH
scale_y = actual_screen_height / VIRTUAL_HEIGHT

CELL_SIZE_SCALED = 45 * scale_x
COLLECT_ITEM_SIZE_SCALED = 20 * scale_x

# General Settings
FPS = 70
MAX_LEVEL = 3  # Maximum number of levels in the game

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)

# Sizes
collect_item_size = 20
PLAYER_SIZE = int(30 * scale_x) 
BULLET_SIZE = int(2 * scale_x)
BULLET_SPEED = int(7 * scale_x)
ZOMBIE_SIZE = int(35 * scale_x)
ZOMBIE_SPEED = int(1 * scale_x)
torch_radius = int(180 * scale_x)

PLAYER_SPEED = int(2*scale_x)

# Paths
current_path = pathlib.Path().absolute()

assets_dir = str(current_path) + "/assets"
images_dir = assets_dir + "/images"
sounds_dir = assets_dir + "/sound_effect"
levels_dir = assets_dir + "/levels"



# Asset Files
bullet_image = pygame.image.load(images_dir + "/bullet.png")
health_image = pygame.image.load(images_dir + "/health.png")
akm_image = pygame.image.load(images_dir + "/AKM.png")
rifle_ammo_image = pygame.image.load(images_dir + "/rifle_ammo.png")
shotgun_image = pygame.image.load(images_dir + "/shotgun.png")
shotgun_ammo_image = pygame.image.load(images_dir + "/shotgun_bullet.png")
piston_ammo_image = pygame.image.load(images_dir + "/piston_bullet.png")
bg_image = pygame.image.load(images_dir + "/background.jpg")
wall_image = pygame.image.load(images_dir + "/wall.png")
breakable_wall_image = pygame.image.load(images_dir + "/break_wall.png")
dead_zombie_image = pygame.image.load(images_dir + "/dead_zombie.png")

# Sound Files
gun_pickup_sound = pygame.mixer.Sound(sounds_dir + "/gun_pickup.mp3")
item_pickup_sound = pygame.mixer.Sound(sounds_dir + "/collect_item.mp3")
death_sound = pygame.mixer.Sound(sounds_dir + "/death.mp3")
victory_sound = pygame.mixer.Sound(sounds_dir + "/victory_sound.mp3")
loose_sound = pygame.mixer.Sound(sounds_dir + "/loose.mp3")
