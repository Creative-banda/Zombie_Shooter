import pygame
import random, json
from extra.zombie_player import Player
from extra.zombie import Zombie
from extra.zombie_settings import *
from extra.spatial_grid import SpatialGrid

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Create the screen with the device resolution
screen = pygame.display.set_mode((actual_screen_width, actual_screen_height))
pygame.display.set_caption("Zombie Shooter")

background_music.play(-1)  # Play the background music on loop

class Camera:
    
    def __init__(self, width, height, player):
        self.camera = pygame.Rect(player.x, player.y, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        # Adjust the position of an entity based on the camera offset
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        # Center the camera on the target (usually the player)
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)
        self.camera.x += (x - self.camera.x) * 0.02  # Smoothly move the camera to the target
        self.camera.y += (y - self.camera.y) * 0.02



def get_camera_view_rect(camera, padding=0):
    # World-space rect for visible area (with padding to reduce pop-in)
    return pygame.Rect(
        int(-camera.camera.x - padding),
        int(-camera.camera.y - padding),
        int(camera.width + padding * 2),
        int(camera.height + padding * 2),
    )

def build_wall_grid(walls):
    grid = SpatialGrid(CELL_SIZE_SCALED)
    grid.build(walls, lambda item: item[0].rect)
    return grid

class Wall:
    def __init__(self, x, y, image, health=100):
        self.x = x
        self.y = y
        self.image = image
        self.health = health  # Health of the wall
        self.rect = pygame.Rect(x, y, CELL_SIZE_SCALED, CELL_SIZE_SCALED)  # Define the rectangle for collision and placement
        self.image = pygame.transform.scale(self.image, (CELL_SIZE_SCALED, CELL_SIZE_SCALED))  # Scale the image to the cell size

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
        self.rect = self.image.get_rect(topleft=(x, y))  # Add rect for camera compatibility

    def draw(self, screen, camera=None):
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering without camera

def create_map(level=1):
    global  bg_image

    walls = []
    zombies = []
    guns = []
    dead_body = []
    blood = []
    pickups = {"ammo": [], "health": []}
    player_start = None
    
    # Load the level 1 as json file 
    with open(f"{LEVELS_DIR}/level{level}.json") as file:
        maze_layout = json.load(file)
    
    height = len(maze_layout)
    width = len(maze_layout[0])

    bg_image = pygame.transform.scale(bg_image, (width * CELL_SIZE_SCALED, height * CELL_SIZE_SCALED))

    
    for y, row in enumerate(maze_layout):
        for x, cell in enumerate(row):
            
            world_x = x * CELL_SIZE_SCALED
            world_y = y * CELL_SIZE_SCALED
            
            if cell == 1:  # Wall
                walls.append((Wall(world_x, world_y, wall_image),"unbreakable"))
            elif cell == 2:  # Ammo pickup
                pickups["ammo"].append((PickUp(world_x, world_y, piston_ammo_image, COLLECT_ITEM_SIZE_SCALED, COLLECT_ITEM_SIZE_SCALED), "handgun"))
            elif cell == 3:  # Health pickup
                pickups["health"].append(PickUp(world_x, world_y, health_image, COLLECT_ITEM_SIZE_SCALED, COLLECT_ITEM_SIZE_SCALED))
            elif cell == 4:  # Zombie
                zombies.append(Zombie(world_x, world_y))
            elif cell == 5:  # Player start
                player_start = (world_x, world_y)
            elif cell == 6:
                walls.append((Wall(world_x, world_y, breakable_wall_image),"breakable"))
            elif cell == 7:
                guns.append((PickUp(world_x, world_y, akm_image, COLLECT_ITEM_SIZE_SCALED , COLLECT_ITEM_SIZE_SCALED * 2), "akm"))
            elif cell == 8:
                guns.append((PickUp(world_x, world_y, shotgun_image, COLLECT_ITEM_SIZE_SCALED , COLLECT_ITEM_SIZE_SCALED * 2), "shotgun"))
            elif cell == 9:
                pickups['ammo'].append((PickUp(world_x, world_y, shotgun_ammo_image, COLLECT_ITEM_SIZE_SCALED, COLLECT_ITEM_SIZE_SCALED), "shotgun"))
            elif cell == 10:
                pickups['ammo'].append((PickUp(world_x, world_y, rifle_ammo_image, COLLECT_ITEM_SIZE_SCALED, COLLECT_ITEM_SIZE_SCALED), "rifle"))
            elif cell == 11:
                lis = [0,1,2]
                random_body = random.choice(lis)
                img = pygame.image.load(f"{IMAGES_DIR}/dead_body/{random_body}.png").convert_alpha()
                
                # do a random rotate
                img = pygame.transform.rotate(img, random.randint(0, 360))
                dead_body.append(PickUp(world_x, world_y, img, PLAYER_SIZE, PLAYER_SIZE))
            elif cell == 12:
                lis = [1,2,4,5,6]
                random_body = random.choice(lis)
                img = pygame.image.load(f"{IMAGES_DIR}/blood/{random_body}.png").convert_alpha()
                
                # do a random rotate
                img = pygame.transform.rotate(img, random.randint(0, 360))
                blood.append(PickUp(world_x, world_y, img, PLAYER_SIZE * 2, PLAYER_SIZE * 2))
            
                
    
    return walls, player_start, zombies, pickups, guns, dead_body, blood

def check_pickups(player, pickups, guns, logic_rect=None):
    # Check for ammo pickups
    for ammo,ammotype in pickups["ammo"]:
        if logic_rect and not logic_rect.colliderect(ammo.rect):
            continue
        if (player.x < ammo.x + 10 and player.x + PLAYER_SIZE > ammo.x and
            player.y < ammo.y + 10 and player.y + PLAYER_SIZE > ammo.y):
            if ammotype == "handgun":
                player.gun_info['handgun']['ammo'] += 15
            elif ammotype == "rifle":
                player.gun_info['rifle']['ammo'] += 20
            elif ammotype == "shotgun":
                player.gun_info['shotgun']['ammo'] += 10
            pickups["ammo"].remove((ammo, ammotype))  # Remove the pickup
            item_pickup_sound.play()

    # Check for health pickups
    for health in pickups["health"][:]:
        if logic_rect and not logic_rect.colliderect(health.rect):
            continue
        if (player.x < health.x + 10 and player.x + PLAYER_SIZE > health.x and
            player.y < health.y + 10 and player.y + PLAYER_SIZE > health.y and player.health < 100):
            player.health = min(player.health + 40, 100)  # Add health, max 100
            pickups["health"].remove(health)  # Remove the pickup
            item_pickup_sound.play()
    
    for gun, gun_type in guns[:]:
        if logic_rect and not logic_rect.colliderect(gun.rect):
            continue

        if (player.x < gun.x + 10 and player.x + PLAYER_SIZE > gun.x and player.y < gun.y + 10 and player.y + PLAYER_SIZE > gun.y):
            if gun_type == "akm":
                player.isRifle = True
            elif gun_type == "shotgun":
                player.isShotgun = True
            guns.remove((gun, gun_type))  # Remove the pickup
            gun_pickup_sound.play()

def create_fading_torch(radius):
    torch_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    # Here Alpha 0 mean fully transparent and 255 mean fully opaque
    for i in range(radius, 0, -1):
        alpha = int(255 * (i / radius))  # Gradually reduce alpha
        color = (0, 0, 0, 255 - alpha)  # Darken towards the edge
        pygame.draw.circle(torch_surface, color, (radius, radius), i)
    return torch_surface

def main():
    current_level = 1

    # Setting all the necessary variables to start the game
    clock = pygame.time.Clock()
    walls, player_start, zombies, pickups, guns, dead_body, blood = create_map(current_level)
    wall_grid = build_wall_grid(walls)
    zombie_grid = SpatialGrid(ZOMBIE_SIZE)
    
    player = Player(actual_screen_width , actual_screen_height, gun_info)

    player.x, player.y = player_start  # Set player's starting position
    running = True
    game_over = False
    won = False
    death_sound_played = False
    font = pygame.font.Font(None, 36)
    victory_sound_played = False

    # This text_width is used to display the zombie count in the right corner of the screen
    text_for_length = font.render(f"Zombies: {len(zombies)}", True, WHITE)
    text_width = text_for_length.get_width()
    
    # Initialize the camera
    camera = Camera(actual_screen_width , actual_screen_height, player)
    bullet_pos = (0, 0)
    
    # Generate the flashlight gradient
    torch_surface = create_fading_torch(TORCH_RADIUS)
    darkness = pygame.Surface((actual_screen_width , actual_screen_height), pygame.SRCALPHA)
    
    dead_zombie_list = []

    while running:    
        dt = clock.tick(0) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT :
                running = False
                
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                running = False
            
            if keys[pygame.K_SPACE]:
                player.shoot()
            elif keys[pygame.K_1]:
                player.current_gun = "handgun"
            elif keys[pygame.K_2] and player.isRifle:
                player.current_gun = "rifle"
            elif keys[pygame.K_3] and player.isShotgun:
                player.current_gun = "shotgun"
            elif keys[pygame.K_r]  and not player.isReloading:
                player.reload()

        # Clear the screen
        screen.blit(bg_image, camera.apply(walls[0][0]))  # Apply camera offset to the background image

        query_padding = int(CELL_SIZE_SCALED * 2)
        
        if not game_over:
            # Update the camera to follow the player
            camera.update(player)

            # Move the player (only check nearby walls)
            player_rect = pygame.Rect(player.x, player.y, PLAYER_SIZE, PLAYER_SIZE)
            player_query = player_rect.inflate(query_padding, query_padding)
            near_walls = wall_grid.query_rect(player_query)
            player.move(near_walls, dt)
            player.update_animation()

            # Update bullets
            zombie_grid.build(zombies, lambda z: z.rect)
            player.update_bullets(walls, zombies, dead_zombie_list, dt, wall_grid, zombie_grid)
            
            # Check win/lose conditions
            if player.health <= 0:
                game_over = True
                player.alive = False
            elif len(zombies) == 0:
                won = True
                game_over = True

        # Build culling rects for visible objects and active logic
        cull_padding = int(max(CELL_SIZE_SCALED, ZOMBIE_SIZE, PLAYER_SIZE))
        view_rect = get_camera_view_rect(camera, cull_padding)
        logic_padding = int(max(actual_screen_width, actual_screen_height))
        logic_rect = pygame.Rect(
            int(player.x - logic_padding),
            int(player.y - logic_padding),
            int(logic_padding * 2 + PLAYER_SIZE),
            int(logic_padding * 2 + PLAYER_SIZE),
        )

        if not game_over:
            # Check for pickups (only when in logic range)
            check_pickups(player, pickups, guns, logic_rect)

        # Draw walls
        for wall, _ in walls:
            if view_rect.colliderect(wall.rect):
                wall.draw(screen, camera)

        # Draw pickups
        for ammo,_ in pickups["ammo"]:
            if view_rect.colliderect(ammo.rect):
                ammo.draw(screen, camera)

        for health in pickups["health"]:
            if view_rect.colliderect(health.rect):
                health.draw(screen, camera)
        
        # Draw blood
        for bloods in blood:
            if view_rect.colliderect(bloods.rect):
                bloods.draw(screen, camera)
            
        # Draw dead body
        for body in dead_body:
            if view_rect.colliderect(body.rect):
                body.draw(screen, camera)
        # Draw guns
        for gun,_ in guns:
            if view_rect.colliderect(gun.rect):
                gun.draw(screen, camera)
            
        # Draw dead zombie
        for dead_zombie in dead_zombie_list:
            if view_rect.colliderect(dead_zombie.rect):
                screen.blit(dead_zombie_image, camera.apply(dead_zombie))

        # Draw player
        player.draw(screen, camera)

        # Draw zombies
        for zombie in zombies:
            # Keep rect in sync for culling checks
            zombie.rect.topleft = (zombie.x, zombie.y)

            if not game_over and logic_rect.colliderect(zombie.rect):
                zombie_query = zombie.rect.inflate(query_padding, query_padding)
                near_walls = wall_grid.query_rect(zombie_query)
                los_rect = pygame.Rect(
                    int(min(zombie.x, player.x)),
                    int(min(zombie.y, player.y)),
                    int(abs(zombie.x - player.x) + ZOMBIE_SIZE),
                    int(abs(zombie.y - player.y) + ZOMBIE_SIZE),
                )
                los_walls = wall_grid.query_rect(los_rect)
                zombie.check_for_player(player)
                zombie.update_direction()
                zombie.move_towards_player(player, near_walls, dt, los_walls)

            if view_rect.colliderect(zombie.rect):
                zombie.draw(screen, camera)

                

        # Draw bullets
        for bullet in player.bullets:
            if view_rect.collidepoint(bullet["x"], bullet["y"]):
                if camera:
                    bullet_pos = (int(bullet["x"] + camera.camera.x), int(bullet["y"] + camera.camera.y))
                else:
                    bullet_pos = (int(bullet["x"]), int(bullet["y"]))
                pygame.draw.circle(screen, RED, bullet_pos, BULLET_SIZE)

        # Create the darkness overlay
        darkness.fill((0, 0, 0, 250))

        # Blit the torchlight effect onto the darkness overlay
        torch_x = player.x + PLAYER_SIZE // 2 - TORCH_RADIUS + camera.camera.topleft[0]
        torch_y = player.y + PLAYER_SIZE // 2 - TORCH_RADIUS + camera.camera.topleft[1]
        
        darkness.blit(torch_surface, (torch_x, torch_y), special_flags=pygame.BLEND_RGBA_SUB)

        # Apply the darkness overlay to the screen
        screen.blit(darkness, (0, 0))

        # Draw HUD (ammo, health)
        ammo_text = font.render(f"Total: {player.gun_info[player.current_gun]['ammo']}", True, WHITE)
        health_text = font.render(f"Health: {player.health}", True, WHITE)
        screen.blit(ammo_text, (10, 10))
        screen.blit(health_text, (10, 50))

        ammo_text = f"Ammo : {player.gun_info[player.current_gun]['remaining_ammo']} "
        screen.blit(font.render(ammo_text, True, WHITE), (actual_screen_width // 2, 10))

        # display the zombie in area
        zombie_text = font.render(f"Zombies: {len(zombies)}", True, WHITE)
        screen.blit(zombie_text, (actual_screen_width - text_width, 10))
        
        # Display game FPS in the bottom left corner
        fps_text = font.render(f"FPS: {int(clock.get_fps())}", True, WHITE)
        screen.blit(fps_text, (10, actual_screen_height - 100))
        
        # Display the current level in the bottom right corner
        level_text = font.render(f"Level: {current_level}", True, WHITE)
        screen.blit(level_text, (actual_screen_width - 100, actual_screen_height - 100))


        # Game over screen
        if not player.alive:
            if not death_sound_played and not won:  # Play death sound only once
                death_sound.play()
                loose_sound.play()
                death_sound_played = True
            text = "Game Over! Press 'R' to restart"  
            game_over_text = font.render(text, True, WHITE)
            text_rect = game_over_text.get_rect(center=(actual_screen_width / 2, actual_screen_height / 2))
            screen.blit(game_over_text, text_rect)   
            # Check for restart input
            pygame.mixer.music.fadeout(1000)  # Fade out over 2 seconds
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                # Reset game state
                walls, player_start, zombies, pickups, guns, dead_body, blood = create_map(current_level)
                wall_grid = build_wall_grid(walls)
                zombie_grid = SpatialGrid(ZOMBIE_SIZE)
                player = Player(actual_screen_width , actual_screen_height, gun_info)

                player.x, player.y = player_start  # Set player's starting position again
                game_over = False
                won = False
                death_sound_played = False
                dead_zombie_list = []

                
                # Play the background music again
                loose_sound.stop()
                background_music.play(-1)
                        
        elif won and player.alive:
            text = "You Win!"
            if not victory_sound_played:
                victory_sound.play()
                victory_sound_played = True
                current_level += 1
            if current_level > MAX_LEVEL:
                winner_text = font.render("Congratulations! You Completed the game!", True, WHITE)
                winner_rect = winner_text.get_rect(center=(actual_screen_width / 2, actual_screen_height / 2 + 50))
                screen.blit(winner_text, winner_rect)
            else:
                walls, player_start, zombies, pickups, guns, dead_body, blood = create_map(current_level)
                wall_grid = build_wall_grid(walls)
                zombie_grid = SpatialGrid(ZOMBIE_SIZE)
                player.x, player.y = player_start  # Set player's starting position again
                player.is_Walking_Sound = False
                game_over = False
                won = False
                victory_sound_played = False 
                dead_zombie_list = []
        
        # Update the display
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
