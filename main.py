import pygame
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
CELL_SIZE = 20
PLAYER_SIZE = 18
ZOMBIE_SIZE = 18

BULLET_SIZE = 2 

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
WALL_BUFFER = 2  # pixels to stay away from walls
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)


# Load images
player_image = "assets/player.png"
zombie = "assets/zombie.png"
bullet_image = pygame.image.load("assets/bullet.png")
health_image = pygame.image.load("assets/health.png")
bg_image = pygame.image.load("assets/background.jpg")
wall_image = pygame.image.load("assets/wall2.png")
wall_image = pygame.transform.scale(wall_image, (CELL_SIZE, CELL_SIZE))  # Scale the image to the cell size
BACKGROUND = pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))

# Create the window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Zombie Maze Escape")
previous_key = None


class Player:
    
    def __init__(self, image_path):
        # Load the player image and scale it
        self.original_image = pygame.image.load(image_path).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (PLAYER_SIZE, PLAYER_SIZE))
        self.image = self.original_image  # Current image to display
        
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
        if keys[pygame.K_s]:  # Move down
            new_y += self.speed
            self.image = pygame.transform.rotate(self.original_image, 270)  # Rotate 180 degrees for down
        if keys[pygame.K_a]:  # Move left
            new_x -= self.speed
            self.image = pygame.transform.rotate(self.original_image, 180)  # Rotate 90 degrees for left
        if keys[pygame.K_d]:  # Move right
            new_x += self.speed
            self.image = pygame.transform.rotate(self.original_image, 0)  # Rotate -90 degrees for right

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



    def shoot(self, target_x, target_y):
        if self.ammo > 0:  # Check if player has ammo
            # Calculate direction vector
            direction_x = target_x - self.x
            direction_y = target_y - self.y
            magnitude = math.sqrt(direction_x ** 2 + direction_y ** 2)
            if magnitude != 0:  # Normalize direction
                direction_x /= magnitude
                direction_y /= magnitude

            # Add the bullet to the list
            bullet_speed = 8  # Speed of the bullet
            bullet = {
                "x": self.x + PLAYER_SIZE // 2,
                "y": self.y + PLAYER_SIZE // 2,
                "dx": direction_x * bullet_speed,
                "dy": direction_y * bullet_speed
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
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.speed = 1
        self.health = 100
        
        # Load and scale the zombie image
        self.original_image = pygame.image.load(image).convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (ZOMBIE_SIZE, ZOMBIE_SIZE))
        self.image = self.original_image  # Current image to display

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
                        self.x = new_x
                        self.y = new_y
                else:
                    self.x = new_x
                    self.y = new_y
            else:
                self.x = new_x
                self.y = new_y

            # Update the zombie's image based on movement direction
            self.update_direction(dx, dy)  # Call the method here

    def update_direction(self, dx, dy):
        """
        Update the zombie's image rotation based on movement direction.
        """
        if abs(dx) > abs(dy):  # Horizontal movement
            if dx > 0:
                self.image = pygame.transform.rotate(self.original_image, 270)  # Right
            else:
                self.image = pygame.transform.rotate(self.original_image, 90)  # Left
        else:  # Vertical movement
            if dy > 0:
                self.image = pygame.transform.rotate(self.original_image, 180)  # Down
            else:
                self.image = self.original_image  # Up (no rotation)

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))


class Wall:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))  # Define the rectangle for collision and placement

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))  # Draw the image at its position

class AmmoPickup:
    def __init__(self, x, y, image, amount=5):  
        self.x = x
        self.y = y
        self.image = image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (10, 10))
        self.amount = amount
    
    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))

class HealthPickup:
    def __init__(self, x, y, image, amount=20):
        self.x = x
        self.y = y
        self.image = image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (10, 10))
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
                zombies.append(Zombie(world_x, world_y, zombie))
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
    clock = pygame.time.Clock()
    walls, player_start, zombies, pickups = create_maze()
    
    # Initialize player with only the image path

    player = Player("assets/player.png")
    player.x, player.y = player_start  # Set player's starting position

    running = True
    game_over = False
    won = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                player.shoot(mouse_x, mouse_y)

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

        # Drawing
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

        # Draw HUD
        font = pygame.font.Font(None, 36)
        ammo_text = font.render(f"Ammo: {player.ammo}", True, WHITE)
        health_text = font.render(f"Health: {player.health}", True, WHITE)
        screen.blit(ammo_text, (10, 10))
        screen.blit(health_text, (10, 50))

        # Game over screen
        if game_over:
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
                player = Player(player_image)  # Reinitialize player
                player.x, player.y = player_start  # Set player's starting position
                game_over = False
                won = False

        # Update the display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()