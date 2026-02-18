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
# Note: screen is already created in zombie_settings.py but we can redefine it here if needed
# though using the one from zombie_settings.py is better for .convert() consistency.
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
        self.health = health  # Health of the wall
        self.rect = pygame.Rect(x, y, CELL_SIZE_SCALED, CELL_SIZE_SCALED)
        # Use pre-scaled image or scale it once
        self.image = pygame.transform.scale(image, (CELL_SIZE_SCALED, CELL_SIZE_SCALED)).convert_alpha()

    def draw(self, screen, camera=None):
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
        self.image = pygame.transform.scale(image, (self.width, self.height)).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))  # Add rect for camera compatibility

    def draw(self, screen, camera=None):
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering without camera

def create_map(level=1):
    global bg_image

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

    bg_image = pygame.transform.scale(bg_image, (width * CELL_SIZE_SCALED, height * CELL_SIZE_SCALED)).convert()

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
                img = load_image(f"{IMAGES_DIR}/dead_body/{random_body}.png")
                # do a random rotate
                img = pygame.transform.rotate(img, random.randint(0, 360))
                dead_body.append(PickUp(world_x, world_y, img, PLAYER_SIZE, PLAYER_SIZE))
            elif cell == 12:
                lis = [1,2,4,5,6]
                random_body = random.choice(lis)
                img = load_image(f"{IMAGES_DIR}/blood/{random_body}.png")
                # do a random rotate
                img = pygame.transform.rotate(img, random.randint(0, 360))
                blood.append(PickUp(world_x, world_y, img, PLAYER_SIZE * 2, PLAYER_SIZE * 2))
    
    return walls, player_start, zombies, pickups, guns, dead_body, blood

def check_pickups(player, pickups, guns, logic_rect=None, static_grid=None):
    # Check for ammo pickups
    for item in pickups["ammo"][:]:
        ammo, ammotype = item
        if logic_rect and not logic_rect.colliderect(ammo.rect):
            continue
        if player.rect.colliderect(ammo.rect):
            if ammotype == "handgun":
                player.gun_info['handgun']['ammo'] += 15
            elif ammotype == "rifle":
                player.gun_info['rifle']['ammo'] += 20
            elif ammotype == "shotgun":
                player.gun_info['shotgun']['ammo'] += 10
            pickups["ammo"].remove(item)
            if static_grid:
                static_grid.remove(ammo, ammo.rect)
            item_pickup_sound.play()

    # Check for health pickups
    for health in pickups["health"][:]:
        if logic_rect and not logic_rect.colliderect(health.rect):
            continue
        if player.rect.colliderect(health.rect) and player.health < 100:
            player.health = min(player.health + 40, 100)
            pickups["health"].remove(health)
            if static_grid:
                static_grid.remove(health, health.rect)
            item_pickup_sound.play()
    
    for item in guns[:]:
        gun, gun_type = item
        if logic_rect and not logic_rect.colliderect(gun.rect):
            continue
        if player.rect.colliderect(gun.rect):
            if gun_type == "akm":
                player.isRifle = True
            elif gun_type == "shotgun":
                player.isShotgun = True
            guns.remove(item)
            if static_grid:
                static_grid.remove(gun, gun.rect)
            gun_pickup_sound.play()

def create_fading_torch(radius):
    torch_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(radius, 0, -1):
        alpha = int(255 * (i / radius))
        color = (0, 0, 0, 255 - alpha)
        pygame.draw.circle(torch_surface, color, (radius, radius), i)
    return torch_surface

def main():
    current_level = 1

    # Setting all the necessary variables to start the game
    clock = pygame.time.Clock()
    walls, player_start, zombies, pickups, guns, dead_body, blood = create_map(current_level)

    # Grid for collisions (only walls)
    wall_grid = build_wall_grid(walls)
    # Grid for rendering all static elements
    static_grid = SpatialGrid(CELL_SIZE_SCALED * 2)
    def rebuild_static_grid():
        static_grid.clear()
        for w in walls: static_grid.add(w[0], w[0].rect)
        for ammo, _ in pickups["ammo"]: static_grid.add(ammo, ammo.rect)
        for h in pickups["health"]: static_grid.add(h, h.rect)
        for g, _ in guns: static_grid.add(g, g.rect)
        for b in blood: static_grid.add(b, b.rect)
        for body in dead_body: static_grid.add(body, body.rect)

    rebuild_static_grid()

    zombie_grid = SpatialGrid(ZOMBIE_SIZE)
    
    player = Player(actual_screen_width , actual_screen_height, gun_info)
    player.x, player.y = player_start
    running = True
    game_over = False
    won = False
    death_sound_played = False
    font = pygame.font.Font(None, 36)
    victory_sound_played = False

    text_for_length = font.render(f"Zombies: {len(zombies)}", True, WHITE)
    text_width = text_for_length.get_width()
    
    camera = Camera(actual_screen_width , actual_screen_height, player)
    
    # Generate the flashlight gradient once
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

        # Update
        if not game_over:
            camera.update(player)

            # Move the player
            player_rect = player.rect
            player_query = player_rect.inflate(CELL_SIZE_SCALED * 2, CELL_SIZE_SCALED * 2)
            near_walls = wall_grid.query_rect(player_query)
            player.move(near_walls, dt)
            player.update_animation()

            # Update bullets
            zombie_grid.build(zombies, lambda z: z.rect)
            player.update_bullets(walls, zombies, dead_zombie_list, dt, wall_grid, zombie_grid)
            
            if player.health <= 0:
                game_over = True
                player.alive = False
            elif len(zombies) == 0:
                won = True
                game_over = True

        # Rendering
        screen.blit(bg_image, camera.apply(walls[0][0]))

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
            check_pickups(player, pickups, guns, logic_rect, static_grid)

        # Draw static entities from grid
        visible_static = static_grid.query_rect(view_rect)
        for entity in visible_static:
            entity.draw(screen, camera)
            
        # Draw dead zombies (not in static grid as they change frequently)
        for dead_zombie in dead_zombie_list:
            if view_rect.colliderect(dead_zombie.rect):
                screen.blit(dead_zombie_image, camera.apply(dead_zombie))

        # Draw player
        player.draw(screen, camera)

        # Draw zombies
        for zombie in zombies:
            # Keep rect in sync
            zombie.rect.topleft = (zombie.x, zombie.y)

            if not game_over and logic_rect.colliderect(zombie.rect):
                zombie_query = zombie.rect.inflate(CELL_SIZE_SCALED * 2, CELL_SIZE_SCALED * 2)
                near_walls = wall_grid.query_rect(zombie_query)
                # For LOS, use a rect that covers zombie and player
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
            # Check if bullet is visible
            if view_rect.collidepoint(bullet["x"], bullet["y"]):
                bullet_scr_x = int(bullet["x"] + camera.camera.x)
                bullet_scr_y = int(bullet["y"] + camera.camera.y)
                screen.blit(bullet_image, (bullet_scr_x - BULLET_SIZE, bullet_scr_y - BULLET_SIZE))

        # Darkness effect
        darkness.fill((0, 0, 0, 250))
        torch_x = player.x + PLAYER_SIZE // 2 - TORCH_RADIUS + camera.camera.topleft[0]
        torch_y = player.y + PLAYER_SIZE // 2 - TORCH_RADIUS + camera.camera.topleft[1]
        darkness.blit(torch_surface, (torch_x, torch_y), special_flags=pygame.BLEND_RGBA_SUB)
        screen.blit(darkness, (0, 0))

        # HUD
        ammo_text = font.render(f"Total: {player.gun_info[player.current_gun]['ammo']}", True, WHITE)
        health_text = font.render(f"Health: {player.health}", True, WHITE)
        screen.blit(ammo_text, (10, 10))
        screen.blit(health_text, (10, 50))
        screen.blit(font.render(f"Ammo : {player.gun_info[player.current_gun]['remaining_ammo']} ", True, WHITE), (actual_screen_width // 2, 10))
        screen.blit(font.render(f"Zombies: {len(zombies)}", True, WHITE), (actual_screen_width - text_width, 10))
        screen.blit(font.render(f"FPS: {int(clock.get_fps())}", True, WHITE), (10, actual_screen_height - 100))
        screen.blit(font.render(f"Level: {current_level}", True, WHITE), (actual_screen_width - 100, actual_screen_height - 100))

        # Game over / Win screens
        if not player.alive:
            if not death_sound_played and not won:
                death_sound.play()
                loose_sound.play()
                death_sound_played = True
            game_over_text = font.render("Game Over! Press 'R' to restart", True, WHITE)
            text_rect = game_over_text.get_rect(center=(actual_screen_width / 2, actual_screen_height / 2))
            screen.blit(game_over_text, text_rect)   
            pygame.mixer.music.fadeout(1000)
            if pygame.key.get_pressed()[pygame.K_r]:
                walls, player_start, zombies, pickups, guns, dead_body, blood = create_map(current_level)
                wall_grid = build_wall_grid(walls)
                rebuild_static_grid()
                player = Player(actual_screen_width , actual_screen_height, gun_info)
                player.x, player.y = player_start
                game_over = False
                won = False
                death_sound_played = False
                dead_zombie_list = []
                loose_sound.stop()
                background_music.play(-1)
                        
        elif won and player.alive:
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
                rebuild_static_grid()
                player.x, player.y = player_start
                player.is_Walking_Sound = False
                game_over = False
                won = False
                victory_sound_played = False 
                dead_zombie_list = []
        
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
