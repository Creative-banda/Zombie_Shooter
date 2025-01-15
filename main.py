import pygame
from zombie import Zombie, ZOMBIE_SIZE
import random, json
from player import Player, PLAYER_SIZE, BULLET_SIZE, CELL_SIZE, PLAYER_SIZE, gun_info

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
COLLECT_ITEM_SIZE = 20
FPS = 60
MAX_LEVEL = 3  # Maximum number of levels in the game

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0) 
GREEN = (0, 255, 0) # Currently no use but maybe in future we can use it
GRAY = (128, 128, 128) # Currently no use but maybe in future we can use it

torch_radius = 180


# player background music

pygame.mixer.music.load('assets/sound_effect/background_music.mp3')
pygame.mixer.music.play(-1, 0.0)
pygame.mixer.music.set_volume(0.5)



# Load images
player_image = "assets/images/player.png"
bullet_image = pygame.image.load("assets/images/bullet.png")
health_image = pygame.image.load("assets/images/health.png")

akm_image = pygame.image.load("assets/images/AKM.png")
rifle_ammo_image = pygame.image.load("assets/images/rifle_ammo.png")

shotgun_image = pygame.image.load("assets/images/shotgun.png")
shotgun_ammo_image = pygame.image.load("assets/images/shotgun_bullet.png")

piston_ammo_image = pygame.image.load("assets/images/piston_bullet.png")

bg_image = pygame.image.load("assets/images/bg_image.jpg")
BACKGROUND = pygame.transform.scale(bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT))

gun_pickup_sound = pygame.mixer.Sound('assets/sound_effect/gun_pickup.mp3')
item_pickup_sound = pygame.mixer.Sound('assets/sound_effect/collect_bullet.mp3')

wall_image = pygame.image.load("assets/images/wall3.PNG")
wall_image = pygame.transform.scale(wall_image, (CELL_SIZE, CELL_SIZE))  # Scale the image to the cell size

# brekable wall image

breakable_wall_image = pygame.image.load("assets/images/break_wall.png")
breakable_wall_image = pygame.transform.scale(breakable_wall_image, (CELL_SIZE, CELL_SIZE))  # Scale the image to the cell size



# load music and sound 

death_sound = pygame.mixer.Sound('assets/sound_effect/death.mp3')
victory_sound = pygame.mixer.Sound('assets/sound_effect/victory_sound.mp3')
loose_sound = pygame.mixer.Sound('assets/sound_effect/loose.mp3')
# Create the window
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Zombie Maze Escape")
previous_key = None

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


class PickUp:
    def __init__(self, x, y, image, height, width, amount=5):
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.image = image.convert_alpha()
        self.image = pygame.transform.scale(self.image, (self.width, self.height))  # Scale the image to the cell size
        self.amount = amount
        self.rect = self.image.get_rect(topleft=(x, y))  # Add rect for camera compatibility

    def draw(self, screen, camera=None):
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering without camera


def create_map(level=3):
    walls = []
    zombies = []
    guns = []
    dead_body = []
    blood = []
    pickups = {"ammo": [], "health": []}
    player_start = None
    
    # Load the level 1 as json file 
    with open(f"assets/levels/level{level}.json") as file:
        maze_layout = json.load(file)

    
    for y, row in enumerate(maze_layout):
        for x, cell in enumerate(row):
            
            world_x = x * CELL_SIZE
            world_y = y * CELL_SIZE
            
            if cell == 1:  # Wall
                walls.append((Wall(world_x, world_y, wall_image),"unbreakable"))
            elif cell == 2:  # Ammo pickup
                pickups["ammo"].append((PickUp(world_x, world_y, piston_ammo_image, COLLECT_ITEM_SIZE, COLLECT_ITEM_SIZE), "handgun"))
            elif cell == 3:  # Health pickup
                pickups["health"].append(PickUp(world_x, world_y, health_image, COLLECT_ITEM_SIZE, COLLECT_ITEM_SIZE))
            elif cell == 4:  # Zombie
                zombies.append(Zombie(world_x, world_y))
            elif cell == 5:  # Player start
                player_start = (world_x, world_y)
            elif cell == 6:
                walls.append((Wall(world_x, world_y, breakable_wall_image),"breakable"))
            elif cell == 7:
                guns.append((PickUp(world_x, world_y, akm_image, COLLECT_ITEM_SIZE , COLLECT_ITEM_SIZE * 2), "akm"))
            elif cell == 8:
                guns.append((PickUp(world_x, world_y, shotgun_image, COLLECT_ITEM_SIZE , COLLECT_ITEM_SIZE * 2), "shotgun"))
            elif cell == 9:
                pickups['ammo'].append((PickUp(world_x, world_y, shotgun_ammo_image, COLLECT_ITEM_SIZE, COLLECT_ITEM_SIZE), "shotgun"))
            elif cell == 10:
                pickups['ammo'].append((PickUp(world_x, world_y, rifle_ammo_image, COLLECT_ITEM_SIZE, COLLECT_ITEM_SIZE), "rifle"))
            elif cell == 11:
                lis = [0,1,2]
                random_body = random.choice(lis)
                img = pygame.image.load(f"assets/images/dead_body/{random_body}.png").convert_alpha()
                
                # do a random rotate
                img = pygame.transform.rotate(img, random.randint(0, 360))
                dead_body.append(PickUp(world_x, world_y, img, PLAYER_SIZE, PLAYER_SIZE))
            elif cell == 12:
                lis = [1,2,4,5,6]
                random_body = random.choice(lis)
                img = pygame.image.load(f"assets/images/blood/{random_body}.png").convert_alpha()
                
                # do a random rotate
                img = pygame.transform.rotate(img, random.randint(0, 360))
                blood.append(PickUp(world_x, world_y, img, PLAYER_SIZE * 2, PLAYER_SIZE * 2))
            
                
    
    return walls, player_start, zombies, pickups, guns, dead_body, blood


def check_pickups(player, pickups, guns):
    # Check for ammo pickups
    for ammo,ammotype in pickups["ammo"]:
        if (player.x < ammo.x + 10 and player.x + PLAYER_SIZE > ammo.x and
            player.y < ammo.y + 10 and player.y + PLAYER_SIZE > ammo.y):
            if ammotype == "handgun":
                gun_info['handgun']['ammo'] += 10
            elif ammotype == "rifle":
                gun_info['rifle']['ammo'] += 10
            elif ammotype == "shotgun":
                gun_info['shotgun']['ammo'] += 10
            pickups["ammo"].remove((ammo, ammotype))  # Remove the pickup
            item_pickup_sound.play()

    # Check for health pickups
    for health in pickups["health"][:]:
        if (player.x < health.x + 10 and player.x + PLAYER_SIZE > health.x and
            player.y < health.y + 10 and player.y + PLAYER_SIZE > health.y):
            player.health = min(player.health + 20, 100)  # Add health, max 100
            pickups["health"].remove(health)  # Remove the pickup
            item_pickup_sound.play()
    
    for gun, gun_type in guns[:]:

        if (player.x < gun.x + 10 and player.x + PLAYER_SIZE > gun.x and player.y < gun.y + 10 and player.y + PLAYER_SIZE > gun.y):
            if gun_type == "akm":
                player.isRifle = True
            elif gun_type == "shotgun":
                player.isShotgun = True
            guns.remove((gun, gun_type))  # Remove the pickup
            gun_pickup_sound.play()


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
    walls, player_start, zombies, pickups, guns, dead_body, blood = create_map()
    
    player = Player(WINDOW_WIDTH, WINDOW_HEIGHT)
    player.x, player.y = player_start  # Set player's starting position
    running = True
    game_over = False
    won = False
    death_sound_played = False
    last_hit_time = pygame.time.get_ticks()
    font = pygame.font.Font(None, 36)
    victory_sound_played = False

    # This text_width is used to display the zombie count in the right corner of the screen
    text_for_length = font.render(f"Zombies: {len(zombies)}", True, WHITE)
    text_width = text_for_length.get_width()
    
    # Initialize the camera
    camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT, player)
    bullet_pos = (0, 0)
    
    # Generate the flashlight gradient
    torch_surface = create_fading_torch(torch_radius)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            player.reload()

        elif keys[pygame.K_SPACE] and not player.isReloading:
            player.shoot()
        # Check for 1 press in keyboard
        elif keys[pygame.K_1] and not player.isReloading:
            player.switch_gun("handgun")
        # Check for 2 press in keyboard
        elif keys[pygame.K_2] and player.isRifle and not player.isReloading:
            player.switch_gun("rifle")
        elif keys[pygame.K_3] and player.isShotgun and not player.isReloading:
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
        for ammo,_ in pickups["ammo"]:
            ammo.draw(screen, camera)

        for health in pickups["health"]:
            health.draw(screen, camera)
        
        # Draw blood
        for bloods in blood:
            bloods.draw(screen, camera)
            
        # Draw dead body
        for body in dead_body:
            body.draw(screen, camera)
        # Draw guns
        for gun,_ in guns:
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
        ammo_text = font.render(f"Ammo: {gun_info[player.current_gun]['ammo']}", True, WHITE)
        health_text = font.render(f"Health: {player.health}", True, WHITE)
        screen.blit(ammo_text, (10, 10))
        screen.blit(health_text, (10, 50))

        ammo_text = f"{gun_info[player.current_gun]['remaining_ammo']} / {gun_info[player.current_gun]['ammo']}"
        screen.blit(font.render(ammo_text, True, WHITE), (WINDOW_WIDTH // 2, 10))

        # display the zombie in area

        zombie_text = font.render(f"Zombies: {len(zombies)}", True, WHITE)
        screen.blit(zombie_text, (WINDOW_WIDTH - text_width, 10))
        
        
        # Display game FPS in the bottom left corner
        
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
        screen.blit(fps_text, (10, WINDOW_HEIGHT - 100))

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
                walls, player_start, zombies, pickups, guns, dead_body, blood = create_map()
                player = Player(WINDOW_WIDTH, WINDOW_HEIGHT)
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
                walls, player_start, zombies, pickups, guns, dead_body, blood = create_map()
                player.x, player.y = player_start  # Set player's starting position again
                game_over = False
                won = False
                victory_sound_played = False  
        
        
        # Update the display
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()