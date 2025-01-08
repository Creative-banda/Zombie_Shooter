import pygame
import math
import random, os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
CELL_SIZE = 20
PLAYER_SIZE = 18
ZOMBIE_SIZE = 18
COLLECT_ITEM_SIZE = 15

BULLET_SIZE = 2 

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
BULLET_DAMAGE = 50  # Damage per bullet


# Load images
player_image = "assets/images/player.png"
bullet_image = pygame.image.load("assets/images/bullet.png")
health_image = pygame.image.load("assets/images/health.png")
bg_image = pygame.image.load("assets/images/bg_image.jpg")
wall_image = pygame.image.load("assets/images/wall3.PNG")
wall_image = pygame.transform.scale(wall_image, (CELL_SIZE, CELL_SIZE))  # Scale the image to the cell size
wall_image.set_colorkey(BLACK)  # Set the transparent color to black
BACKGROUND = pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))


# load music and sound 

pygame.mixer.music.load('assets/sound_effect/bg_music.mp3')
pygame.mixer.music.set_volume(0.6)
pygame.mixer.music.play(-1, 0.0)

# Create the window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Zombie Maze Escape")
previous_key = None
ANIMATION_COOLDOWN = 100  # Time between frames (in milliseconds)


class Player:
    
    def __init__(self, image_path):
        # Load the player image and scale it
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (PLAYER_SIZE, PLAYER_SIZE))
        self.image = self.original_image  # Current image to display
        
        self.direction = "right" # default direction
        
        # Set initial position (center of the screen or any default position)
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT // 2
        
        # Movement attributes
        self.speed = 2
        
        # Game attributes
        self.ammo = 10
        self.health = 100
        self.bullets = []  # List to store bullets

    def move(self, walls):
        # Get the state of all keys
        keys = pygame.key.get_pressed()
        
        # Calculate new position based on key presses
        new_x = self.x
        new_y = self.y
        
        if keys[pygame.K_w]:  # Move up
            new_y -= self.speed
            self.image = pygame.transform.rotate(self.original_image, 90)  # No rotation for up
            self.direction = "up"  # Update direction
        if keys[pygame.K_s]:  # Move down
            new_y += self.speed
            self.image = pygame.transform.rotate(self.original_image, 270)  # Rotate 180 degrees for down
            self.direction = "down"  # Update direction
        if keys[pygame.K_a]:  # Move left
            new_x -= self.speed
            self.image = pygame.transform.rotate(self.original_image, 180)  # Rotate 90 degrees for left
            self.direction = "left"  # Update direction
        if keys[pygame.K_d]:  # Move right
            new_x += self.speed
            self.image = pygame.transform.rotate(self.original_image, 0)  # Rotate -90 degrees for right
            self.direction = "right"  # Update direction

        # Check for collisions with walls
        for wall in walls:
            if (new_x + PLAYER_SIZE > wall.x and new_x < wall.x + CELL_SIZE and
                new_y + PLAYER_SIZE > wall.y and new_y < wall.y + CELL_SIZE):
                # Collision detected, undo movement
                if keys[pygame.K_w]:  # If moving up, reset Y
                    new_y = self.y
                if keys[pygame.K_s]:  # If moving down, reset Y
                    new_y = self.y
                if keys[pygame.K_a]:  # If moving left, reset X
                    new_x = self.x
                if keys[pygame.K_d]:  # If moving right, reset X
                    new_x = self.x

        # Update player position
        self.x = new_x
        self.y = new_y

    def shoot(self):
        if self.ammo > 0:  # Check if player has ammo
            # Play the shooting sound
            pygame.mixer.Sound('assets/sound_effect/shoot.wav').play()

            # Calculate bullet direction based on player's facing direction
            if self.direction == "up":
                dx, dy = 0, -1  # Shoot upwards
            elif self.direction == "down":
                dx, dy = 0, 1  # Shoot downwards
            elif self.direction == "left":
                dx, dy = -1, 0  # Shoot to the left
            elif self.direction == "right":
                dx, dy = 1, 0  # Shoot to the right

            # Add the bullet to the list
            bullet_speed = 8  # Speed of the bullet
            bullet = {
                "x": self.x + PLAYER_SIZE // 2,
                "y": self.y + PLAYER_SIZE // 2,
                "dx": dx * bullet_speed,
                "dy": dy * bullet_speed
            }
            self.bullets.append(bullet)
            self.ammo -= 1  # Decrease ammo count


    def update_bullets(self, walls, zombies):
        for bullet in self.bullets[:]:  # Iterate over a copy of the list
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]

            # Remove bullet if it goes off-screen
            if (bullet["x"] < 0 or bullet["x"] > WINDOW_WIDTH or
                bullet["y"] < 0 or bullet["y"] > WINDOW_HEIGHT):
                self.bullets.remove(bullet)
                continue

            # Check for collisions with walls
            for wall in walls:
                if (bullet["x"] > wall.x and bullet["x"] < wall.x + CELL_SIZE and
                    bullet["y"] > wall.y and bullet["y"] < wall.y + CELL_SIZE):
                    self.bullets.remove(bullet)
                    break

            # Check for collisions with zombies
            for zombie in zombies[:]:
                if (bullet["x"] > zombie.x and bullet["x"] < zombie.x + ZOMBIE_SIZE and
                    bullet["y"] > zombie.y and bullet["y"] < zombie.y + ZOMBIE_SIZE):
                    zombie.health -= BULLET_DAMAGE # Reduce zombie health by 50 we can adjust this value as per our need
                    
                    if zombie.health <= 0:
                        
                        # choose a random sound effect for zombie death
                        random_sound = ['zombie_die1', 'zombie_die2', 'zombie_die3']
                        sound = random.choice(random_sound)
                        sound = "assets/sound_effect/" + sound + ".mp3"
                        pygame.mixer.Sound(sound).play()
                        
                        zombies.remove(zombie)  # Remove the zombie
                    self.bullets.remove(bullet)  # Remove the bullet
                    break

    def draw(self, screen):
        # Draw the player image
        screen.blit(self.image, (self.x, self.y))

        # Optionally, draw bullets (if needed)
        for bullet in self.bullets:
            pygame.draw.circle(screen, (255, 0, 0), (int(bullet["x"]), int(bullet["y"])), 3)


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
            for wall in walls:
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
                    if (new_x + ZOMBIE_SIZE > wall.x and 
                        new_x < wall.x + CELL_SIZE and
                        new_y + ZOMBIE_SIZE > wall.y and 
                        new_y < wall.y + CELL_SIZE):
                        can_move_horizontal = False
                        break
                
                # Try vertical movement only
                if not can_move_horizontal:
                    new_x = self.x
                    new_y = self.y + dy
                    can_move_vertical = True
                    
                    for wall in walls:
                        if (new_x + ZOMBIE_SIZE > wall.x and 
                            new_x < wall.x + CELL_SIZE and
                            new_y + ZOMBIE_SIZE > wall.y and 
                            new_y < wall.y + CELL_SIZE):
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

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))


class Wall:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))  # Define the rectangle for collision and placement
        self.image = pygame.transform.scale(self.image, (CELL_SIZE, CELL_SIZE))  # Scale the image to the cell size


    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y)) 

class AmmoPickup:
    def __init__(self, x, y, image, amount=5):  
        self.x = x
        self.y = y
        self.image = image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (COLLECT_ITEM_SIZE, COLLECT_ITEM_SIZE))
        self.amount = amount
    
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

class HealthPickup:
    def __init__(self, x, y, image, amount=20):
        self.x = x
        self.y = y
        self.image = image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (COLLECT_ITEM_SIZE, COLLECT_ITEM_SIZE))
        self.amount = amount
    
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

def create_maze():
    walls = []
    zombies = []
    pickups = {"ammo": [], "health": []}
    player_start = None

    maze_layout = [
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
        "W     W    Z      W    Z     W  W      W",
        "W WWW W WWWWWWW   W WWWWWW W W  W WWW  W",
        "W W    Z  W   W      W  Z  W W  W      W",
        "W W WWWWWW W W WWWWW W WWWWWW W WWWWW  W",
        "W W W  H W W     W       W    W W      W",
        "W W WWWW W WWWWW W WWWWW  WWWWW W WWW  W",
        "W W     P   W    W   W W   Z    W      W",
        "W WWWWWWWWWWW WWWWWW W W WWWWWWWWWWWW  W",
        "W     W   W   A  W   W W        W      W",
        "W WWWWW W WWW WWWW WWW W WWWWWWWW WWWWWW",
        "W       W   Z   W       W W     W      W",
        "W WWWWWWWWWWWWWWWWWWWWWWW W WWW  WWWWWWW",
        "W W             W    W          W      W",
        "W WWWWWWWWW WWWWW WWWWWWWWWWWW WWWW  WWW",
        "W W        W   W         W      W      W",
        "W WWWWWWWWWW W W WWWWWWW W WWWWWW WWWWWW",
        "W Z        W W W       W W      W      W",
        "W WWWWWWWW W W WWWWWWWWW W WWWW WWW WWWW",
        "W          W W       W          W      W",
        "WWWWWWWWW WWWWWWWWWWWWWWW WW WWWWWW WWWW",
        "W     W    Z      W    Z     W  W      W",
        "W WWW W WWWWWWW   W WWWWWW W W   WWWWWWW",
        "W W    Z  W   W      W  Z  W W  W      W",
        "W W WWWWWW W W WWWWW W WWWWWW W WWWWWWWW",
        "W W W  H W W     W       W    W W      W",
        "W W WWWW W WWWWW W WWWWW  WWWWW W WWWWWW",
        "W W     P   W    W   W W   Z    W      W",
        "W    W    A                            W",
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    ]
    
    for y, row in enumerate(maze_layout):
        for x, char in enumerate(row):
            world_x = x * CELL_SIZE
            world_y = y * CELL_SIZE
            
            if char == 'W':
                walls.append(Wall(world_x, world_y, wall_image))
            elif char == 'P':
                player_start = (world_x, world_y)
            elif char == 'Z':
                zombies.append(Zombie(world_x, world_y))
            elif char == 'A':
                pickups["ammo"].append(AmmoPickup(world_x, world_y, bullet_image))
            elif char == 'H':
                pickups["health"].append(HealthPickup(world_x, world_y, health_image))
    
    return walls, player_start, zombies, pickups

def check_pickups(player, pickups):
    # Check for ammo pickups
    for ammo in pickups["ammo"][:]:
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

def main():
    # setting all the necessary variables to start the game
    
    clock = pygame.time.Clock()
    walls, player_start, zombies, pickups = create_maze()
    
    player = Player(player_image)
    player.x, player.y = player_start  # Set player's starting position
    running = True
    game_over = False
    won = False
    death_sound_played = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and not game_over:
                if event.key == pygame.K_SPACE:  # Space bar pressed
                    player.shoot()  # Shoot in the player's direction

        if not game_over:
            # Check for pickups
            check_pickups(player, pickups)

            # Move the player
            player.move(walls)

            # Update bullets
            player.update_bullets(walls, zombies)

            # Check win/lose conditions
            if player.health <= 0:
                game_over = True
            elif len(zombies) == 0:
                won = True
                game_over = True

        # Drawing background image
        screen.blit(BACKGROUND, (0, 0))

        # Draw walls
        for wall in walls:
            wall.draw(screen)

        # Draw pickups
        for ammo in pickups["ammo"]:
            ammo.draw(screen)
        for health in pickups["health"]:
            health.draw(screen)

        # Draw player
        player.draw(screen)

        # Draw zombies
        for zombie in zombies:
            zombie.move_towards_player(player, walls)
            zombie.draw(screen)
            
            # Check for zombie collision with player
            if (zombie.x < player.x + PLAYER_SIZE and zombie.x + ZOMBIE_SIZE > player.x and
                zombie.y < player.y + PLAYER_SIZE and zombie.y + ZOMBIE_SIZE > player.y):
                if player.health > 0:
                    player.health -= 1  # Reduce player health on collision

        # Draw bullets
        for bullet in player.bullets:
            pygame.draw.circle(screen, BLUE, (int(bullet["x"]), int(bullet["y"])), BULLET_SIZE)

        # Draw HUD mean Heads Up Display like (ammo, health)
        font = pygame.font.Font(None, 36)
        ammo_text = font.render(f"Ammo: {player.ammo}", True, WHITE)
        health_text = font.render(f"Health: {player.health}", True, WHITE)
        screen.blit(ammo_text, (10, 10))
        screen.blit(health_text, (10, 50))

        # Game over screen
        if game_over:
            
            # playing death sound effect
            
            if not death_sound_played:  # Play death sound only once if we don't make this condtion it will play sound again and again
                pygame.mixer.Sound('assets/sound_effect/death.mp3').play()
                death_sound_played = True  # Set the flag to True to prevent playing again
                        
            pygame.mixer.music.fadeout(1000)  # Fade out over 2 seconds
            text = "You Win!" if won else "Game Over!"
            game_over_text = font.render(text, True, WHITE)
            text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
            screen.blit(game_over_text, text_rect)

            # Add a restart option
            restart_text = font.render("Press R to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 50))
            screen.blit(restart_text, restart_rect)

            # Check for restart input
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                # Reset game state
                walls, player_start, zombies, pickups = create_maze()
                player = Player(player_image)  # Reinitialize player object for next round
                player.x, player.y = player_start  # Set player's starting position again
                game_over = False
                won = False
                death_sound_played = False
                
                # play the background music again
                pygame.mixer.music.play(-1, 0.0)

        # Update the display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()