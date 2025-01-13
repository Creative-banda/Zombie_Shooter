import pygame
import math
import random, os, json
from player import Player, PLAYER_SIZE, BULLET_SIZE, CELL_SIZE, PLAYER_SIZE

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
CELL_SIZE = 40
ZOMBIE_SIZE = 30
COLLECT_ITEM_SIZE = 20
FPS = 60
MAX_LEVEL = 3  # Maximum number of levels in the game

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0) # Currently no use but maybe in future we can use it
GREEN = (0, 255, 0) # Currently no use but maybe in future we can use it
GRAY = (128, 128, 128) # Currently no use but maybe in future we can use it

torch_radius = 180



# Load images
player_image = "assets/images/player.png"
bullet_image = pygame.image.load("assets/images/bullet.png")
health_image = pygame.image.load("assets/images/health.png")
akm_image = pygame.image.load("assets/images/AKM.png")
shotgun_image = pygame.image.load("assets/images/shotgun.png")

bg_image = pygame.image.load("assets/images/bg_image.jpg")
BACKGROUND = pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))

wall_image = pygame.image.load("assets/images/wall3.PNG")
wall_image = pygame.transform.scale(wall_image, (CELL_SIZE, CELL_SIZE))  # Scale the image to the cell size

# brekable wall image

breakable_wall_image = pygame.image.load("assets/images/break_wall.png")
breakable_wall_image = pygame.transform.scale(breakable_wall_image, (CELL_SIZE, CELL_SIZE))  # Scale the image to the cell size

# load music and sound 

pygame.mixer.music.load('assets/sound_effect/bg_music.mp3')
pygame.mixer.music.set_volume(0.2)
pygame.mixer.music.play(-1, 0.0)

death_sound = pygame.mixer.Sound('assets/sound_effect/death.mp3')
victory_sound = pygame.mixer.Sound('assets/sound_effect/victory_sound.mp3')
loose_sound = pygame.mixer.Sound('assets/sound_effect/loose.mp3')
# Create the window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Zombie Maze Escape")
previous_key = None
ANIMATION_COOLDOWN = 100 


class Camera:
    def __init__(self, width, height, player):
        self.camera = pygame.Rect(player.x, player.y, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        # Adjust the position of an entity based on the camera offset
        return entity.rect.move(self.camera.topleft )

    def update(self, target):
        # Center the camera on the target (usually the player)
        x = -target.rect.centerx + int(self.width / 2)

        y = -target.rect.centery + int(self.height / 2)
        self.camera = pygame.Rect(x, y, self.width, self.height)

class Zombie:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 1
        self.health = 100
        self.frame_index = 0 
        self.update_time = pygame.time.get_ticks()
        self.animation_list = []
        
        # Load animation frames
        for i in range(6):  
            img_path = os.path.join('assets/images/zombie', f'{i+1}.png')    
            image = pygame.image.load(img_path).convert_alpha()
            # Scale the image
            image = pygame.transform.scale(image, (ZOMBIE_SIZE, ZOMBIE_SIZE))
            self.animation_list.append(image)

        # Current image to display
        self.image = self.animation_list[self.frame_index]
        self.direction = "down"  # Default direction

        # Add a rect attribute for collision and rendering
        self.rect = pygame.Rect(self.x, self.y, ZOMBIE_SIZE, ZOMBIE_SIZE)

    def move_towards_player(self, player, walls):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            dx = dx / distance * self.speed
            dy = dy / distance * self.speed
            
            # Try direct movement first
            new_x = self.x + dx
            new_y = self.y + dy
            
            # Check collision with walls
            direct_path_blocked = False
            for wall, wall_type in walls:  # Unpack the tuple into wall and wall_type
                if (new_x + ZOMBIE_SIZE > wall.x and 
                    new_x < wall.x + CELL_SIZE and
                    new_y + ZOMBIE_SIZE > wall.y and 
                    new_y < wall.y + CELL_SIZE):
                    direct_path_blocked = True
                    break
            
            # Here is the explanation of the code below first zombie try to move directly towards the player if there is no wall in between them
            # if there is a wall in between them then zombie will try to move horizontally or vertically towards the player
            # if both horizontal and vertical movements are blocked then zombie will not move
            
            if direct_path_blocked:
                # Try horizontal movement only
                new_x = self.x + dx
                new_y = self.y
                can_move_horizontal = True
                
                for wall in walls:
                    if (new_x + ZOMBIE_SIZE > wall[0].x and 
                        new_x < wall[0].x + CELL_SIZE and
                        new_y + ZOMBIE_SIZE > wall[0].y and 
                        new_y < wall[0].y + CELL_SIZE):
                        can_move_horizontal = False
                        break
                
                # Try vertical movement only
                if not can_move_horizontal:
                    new_x = self.x
                    new_y = self.y + dy
                    can_move_vertical = True
                    
                    for wall in walls:
                        if (new_x + ZOMBIE_SIZE > wall[0].x and 
                            new_x < wall[0].x + CELL_SIZE and
                            new_y + ZOMBIE_SIZE > wall[0].y and 
                            new_y < wall[0].y + CELL_SIZE):
                            can_move_vertical = False
                            break
                    
                    if can_move_vertical:
                        # Move vertically
                        self.x = new_x 
                        self.y = new_y 
                        # Update direction to face vertical movement
                        if dy > 0:
                            self.direction = "down"
                        else:
                            self.direction = "up"
                    else:
                        # If both horizontal and vertical movements are blocked, do nothing
                        pass
                else:
                    # Move horizontally
                    self.x = new_x
                    self.y = new_y
                    # Update direction to face horizontal movement
                    if dx > 0:
                        self.direction = "right"
                    else:
                        self.direction = "left"
            else:
                # Move directly towards the player
                self.x = new_x
                self.y = new_y
                # Update direction based on movement
                if abs(dx) > abs(dy):  # Horizontal movement
                    if dx > 0:
                        self.direction = "right"
                    else:
                        self.direction = "left"
                else:  # Vertical movement
                    if dy > 0:
                        self.direction = "down"
                    else:
                        self.direction = "up"

            # Update the zombie's animation and direction
            self.update_direction()

            # Update the rect position to match the zombie's current position
            self.rect.topleft = (self.x, self.y)

    def update_direction(self):
        """
        Update the zombie's animation frame and rotate it based on direction.
        """
        # Update animation
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            if self.frame_index >= len(self.animation_list):
                self.frame_index = 0

        # Rotate the current frame based on direction
        if self.direction == "right":
            self.image = pygame.transform.rotate(self.animation_list[self.frame_index], 270)
        elif self.direction == "left":
            self.image = pygame.transform.rotate(self.animation_list[self.frame_index], 90)
        elif self.direction == "down":
            self.image = pygame.transform.rotate(self.animation_list[self.frame_index], 180)
        elif self.direction == "up":
            self.image = self.animation_list[self.frame_index]  # No rotation for up

    def draw(self, screen, camera=None):
        # Update the rect position to match the zombie's current position
        self.rect.topleft = (self.x, self.y)
        
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering


class Guns:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
        self.rect = pygame.Rect(x, y, COLLECT_ITEM_SIZE * 2, COLLECT_ITEM_SIZE * 2)  # Define the rectangle for collision and placement
        self.image = pygame.transform.scale(self.image, (COLLECT_ITEM_SIZE * 2, COLLECT_ITEM_SIZE))  # Scale the image to the cell size

    def draw(self, screen, camera=None):
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering without camera


class Wall:
    def __init__(self, x, y, image, health=100):
        self.x = x
        self.y = y
        self.image = image
        self.health = health  # Health of the wall
        self.rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)  # Define the rectangle for collision and placement
        self.image = pygame.transform.scale(self.image, (CELL_SIZE, CELL_SIZE))  # Scale the image to the cell size

    def draw(self, screen, camera=None):
        # Update the rect position to match the wall's current position
        self.rect.topleft = (self.x, self.y)
        
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering without camera

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            return True
        return False


class AmmoPickup:
    def __init__(self, x, y, image, amount=5):
        self.x = x
        self.y = y
        self.image = image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (COLLECT_ITEM_SIZE, COLLECT_ITEM_SIZE))
        self.amount = amount
        self.rect = self.image.get_rect(topleft=(x, y))  # Add rect for camera compatibility

    def draw(self, screen, camera=None):
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering without camera


class HealthPickup:
    def __init__(self, x, y, image, amount=20):
        self.x = x
        self.y = y
        self.image = image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (COLLECT_ITEM_SIZE, COLLECT_ITEM_SIZE))
        self.amount = amount
        self.rect = self.image.get_rect(topleft=(x, y))  # Add rect for camera compatibility

    def draw(self, screen, camera=None):
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering without camera


def create_map(level=1):
    walls = []
    zombies = []
    guns = []
    pickups = {"ammo": [], "health": []}
    player_start = None
    
    # Load the level 1 as json file 
    with open(f"assets/levels/level{level}.json") as file:
        maze_layout = json.load(file)

    
    for y, row in enumerate(maze_layout):
        if not isinstance(row, (list, tuple)):
            raise TypeError(f"Expected 'row' to be a list or tuple, got {type(row).__name__}.")
        for x, cell in enumerate(row):
            
            world_x = x * CELL_SIZE
            world_y = y * CELL_SIZE
            
            if cell == 1:  # Wall
                walls.append((Wall(world_x, world_y, wall_image),"unbreakable"))
            elif cell == 2:  # Ammo pickup
                pickups["ammo"].append(AmmoPickup(world_x, world_y, bullet_image))
            elif cell == 3:  # Health pickup
                pickups["health"].append(HealthPickup(world_x, world_y, health_image))
            elif cell == 4:  # Zombie
                zombies.append(Zombie(world_x, world_y))
            elif cell == 5:  # Player start
                player_start = (world_x, world_y)
            elif cell == 6:
                walls.append((Wall(world_x, world_y, breakable_wall_image),"breakable"))
            elif cell == 7:
                guns.append((Guns(world_x, world_y, akm_image), "akm"))
            elif cell == 8:
                guns.append((Guns(world_x, world_y, shotgun_image), "shotgun"))
                
    
    return walls, player_start, zombies, pickups, guns



def check_pickups(player, pickups, guns):
    # Check for ammo pickups
    for ammo in pickups["ammo"]:
        if (player.x < ammo.x + 10 and player.x + PLAYER_SIZE > ammo.x and
            player.y < ammo.y + 10 and player.y + PLAYER_SIZE > ammo.y):
            player.ammo += 5  # Add ammo
            pickups["ammo"].remove(ammo)  # Remove the pickup

    # Check for health pickups
    for health in pickups["health"][:]:
        if (player.x < health.x + 10 and player.x + PLAYER_SIZE > health.x and
            player.y < health.y + 10 and player.y + PLAYER_SIZE > health.y):
            player.health = min(player.health + 20, 100)  # Add health, max 100
            pickups["health"].remove(health)  # Remove the pickup
    
    for gun, gun_type in guns[:]:

        if (player.x < gun.x + 10 and player.x + PLAYER_SIZE > gun.x and player.y < gun.y + 10 and player.y + PLAYER_SIZE > gun.y):
            if gun_type == "akm":
                player.isRifle = True
            elif gun_type == "shotgun":
                player.isShotgun = True
            
            guns.remove((gun, gun_type))  # Remove the pickup

def create_fading_torch(radius):
    torch_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(radius, 0, -1):
        alpha = int(255 * (i / radius))  # Gradually reduce alpha
        color = (0, 0, 0, 255 - alpha)  # Darken towards the edge
        pygame.draw.circle(torch_surface, color, (radius, radius), i)
    return torch_surface

def main():
    current_level = 1

    # Setting all the necessary variables to start the game
    clock = pygame.time.Clock()
    walls, player_start, zombies, pickups, guns = create_map()
    
    player = Player(WINDOW_WIDTH, WINDOW_HEIGHT)
    player.x, player.y = player_start  # Set player's starting position
    running = True
    game_over = False
    won = False
    death_sound_played = False
    last_hit_time = pygame.time.get_ticks()
    font = pygame.font.Font(None, 36)
    victory_sound_played = False
    
    # Initialize the camera
    camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT, player)
    bullet_pos = (0, 0)
    
    # Generate the flashlight gradient
    torch_surface = create_fading_torch(torch_radius)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_SPACE:  # Space bar pressed
                    player.shoot()  # Shoot in the player's direction

        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            player.reload()
        # Check for 1 press in keyboard
        elif keys[pygame.K_1]:
            player.switch_gun("handgun")
        # Check for 2 press in keyboard
        elif keys[pygame.K_2] and player.isRifle:
            player.switch_gun("rifle")
        elif keys[pygame.K_3] and player.isShotgun:
            player.switch_gun("shotgun")

        # Clear the screen
        screen.blit(BACKGROUND, (0, 0))

        if not game_over:
            # Check for pickups
            check_pickups(player, pickups, guns)

            # Update the camera to follow the player
            camera.update(player)

            # Move the player
            player.move(walls)
            player.update_animation()

            # Update bullets
            player.update_bullets(walls, zombies)

            # Check win/lose conditions
            if player.health <= 0:
                game_over = True
                player.alive = False
            elif len(zombies) == 0:
                won = True
                game_over = True

        # Draw walls
        for wall in walls:
            wall[0].draw(screen, camera)

        # Draw pickups
        for ammo in pickups["ammo"]:
            ammo.draw(screen, camera)
        for health in pickups["health"]:
            health.draw(screen, camera)
        
        # Draw guns
        for gun,gun_type in guns:
            gun.draw(screen, camera)

        # Draw player
        player.draw(screen, camera)

        # Draw zombies
        for zombie in zombies:
            zombie.move_towards_player(player, walls)
            zombie.draw(screen, camera)
            
            # Check for zombie collision with player
            if (zombie.x < player.x + PLAYER_SIZE and zombie.x + ZOMBIE_SIZE > player.x and
                zombie.y < player.y + PLAYER_SIZE and zombie.y + ZOMBIE_SIZE > player.y):
                if player.health > 0:
                    # Add a timer to prevent playing the sound effect too frequently
                    if pygame.time.get_ticks() - last_hit_time > 1000:  # 1000 milliseconds = 1 second
                        # Play the random damage sound effect
                        music = random.choice(['1', '2', '3', '4', '5'])
                        sound = "assets/sound_effect/damage_sound/" + music + ".mp3"
                        pygame.mixer.Sound(sound).play()
                        last_hit_time = pygame.time.get_ticks()
                        player.health -= 20  # Reduce player health on collision

        # Draw bullets
        for bullet in player.bullets:
            if camera:
                bullet_pos = (int(bullet["x"] + camera.camera.x), int(bullet["y"] + camera.camera.y))
            else:
                bullet_pos = (int(bullet["x"]), int(bullet["y"]))
            pygame.draw.circle(screen, RED, bullet_pos, BULLET_SIZE)
            player.update_bullets(walls, zombies)

        # Create the darkness overlay
        darkness = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        darkness.fill((0, 0, 0, 250))

        # Blit the torchlight effect onto the darkness overlay
        torch_x = player.x + PLAYER_SIZE // 2 - torch_radius + camera.camera.topleft[0]
        torch_y = player.y + PLAYER_SIZE // 2 - torch_radius + camera.camera.topleft[1]
        
        darkness.blit(torch_surface, (torch_x, torch_y), special_flags=pygame.BLEND_RGBA_SUB)

        # Apply the darkness overlay to the screen
        screen.blit(darkness, (0, 0))

        # Draw HUD (ammo, health)
        ammo_text = font.render(f"Ammo: {player.ammo}", True, WHITE)
        health_text = font.render(f"Health: {player.health}", True, WHITE)
        screen.blit(ammo_text, (10, 10))
        screen.blit(health_text, (10, 50))
        # Game over screen
        if not player.alive:
            if not death_sound_played and not won:  # Play death sound only once
                death_sound.play()
                loose_sound.play()
                death_sound_played = True
            text = "Game Over! Press 'R' to restart"  
            game_over_text = font.render(text, True, WHITE)
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
            screen.blit(game_over_text, text_rect)   
            # Check for restart input
            pygame.mixer.music.fadeout(1000)  # Fade out over 2 seconds
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                # Reset game state
                walls, player_start, zombies, pickups, guns = create_map()
                player.x, player.y = player_start  # Set player's starting position again
                game_over = False
                won = False
                death_sound_played = False          
                # Play the background music again
                pygame.mixer.music.play(-1, 0.0)
                        
        elif won and player.alive:
            text = "You Win!"
            if not victory_sound_played:
                victory_sound.play()
                victory_sound_played = True
                current_level += 1
            if current_level > MAX_LEVEL:
                winner_text = font.render("Congratulations! You Completed the game!", True, WHITE)
                winner_rect = winner_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 50))
                screen.blit(winner_text, winner_rect)
            else:
                walls, player_start, zombies, pickups, guns = create_map(current_level)
                player.x, player.y = player_start  # Set player's starting position again
                game_over = False
                won = False
                victory_sound_played = False  
        
        ammo_text = f"{player.remaing_ammo}/{player.ammo}"
        screen.blit(font.render(ammo_text, True, WHITE), (WINDOW_WIDTH // 2, 10))
        
        # Update the display
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()