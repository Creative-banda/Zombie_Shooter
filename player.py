import pygame
import random, copy
import os, math, pathlib
from settings import CELL_SIZE_SCALED, ZOMBIE_SIZE, PLAYER_SIZE, BULLET_SPEED, PLAYER_SPEED


pygame.mixer.init()


ANIMATION_COOLDOWN = 100

# Shotgun settings
BULLET_SPREAD = 45  # Degrees of spread
BULLET_COUNT = 6  # Number of bullets per shotgun shot

# Sound effects
current_path = pathlib.Path().absolute()

walk_sound = pygame.mixer.Sound(str(current_path) +'/assets/sound_effect/player_walk.mp3')



# Gun information

gun_info = {
    "handgun": {
        "damage": 20,
        "ammo": 15,
        "magazine": 6,
        "cooldown": 0,
        "remaining_ammo": 6,
        "sound": str(current_path) +'/assets/sound_effect/gun_sound/handgun.mp3',
        "reloading_sound" : str(current_path) +'/assets/sound_effect/gun_sound/handgun_reload.mp3'
    },
    "rifle": {
        "damage": 50,
        "ammo": 40,
        "magazine": 20,
        "cooldown": 100,
        "remaining_ammo": 20,
        "sound": str(current_path) +'/assets/sound_effect/gun_sound/rifle.mp3',
        "reloading_sound" : str(current_path) +'/assets/sound_effect/gun_sound/rifle_reload.mp3'

    },
    "shotgun": {
        "damage": 100,
        "ammo": 10,
        "magazine": 2,
        "cooldown": 1000,
        "remaining_ammo": 2,
        "sound": str(current_path) +'/assets/sound_effect/gun_sound/shotgun_shot.mp3',
        "reloading_sound" : str(current_path) +'/assets/sound_effect/gun_sound/shotgun_reload.mp3'

    }
}

unchanged_details = copy.deepcopy(gun_info)


class Player:
    
    def __init__(self, WINDOW_WIDTH, WINDOW_HEIGHT):
        self.alive = True
        self.direction = "right"
        self.animation_cool_down = pygame.time.get_ticks()
        self.update_time = pygame.time.get_ticks()
        self.can_shoot = True
        self.isReloading = False
        self.is_Walking_Sound = False

        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT // 2
        self.rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)

        # Animation properties
        self.frame_index = 0
        self.action = 0  # 0: idle, 1: move, 2: reload, 3: shoot
        self.animation_completed = True

        self.ammo = 100
        self.health = 10000
        self.bullets = []
        self.current_gun = "handgun"  # Default gun
        self.isShotgun = False
        self.isRifle = False

        # Initialize animation dictionary
        self.animation_dict = {}

        # Load animations for each gun
        gun_types = ["handgun", "rifle", "shotgun"]  # List of all gun types
        animation_types = ["idle", "move", "reload", "shoot"]  # Animation states

        for gun in gun_types:
            self.animation_dict[gun] = []  # Initialize an empty list for this gun
            for animation in animation_types:
                temp_list = []
                num_of_frames = len(os.listdir(f'{current_path}/assets/images/player/{gun}/{animation}'))
                for i in range(num_of_frames):
                    img = pygame.image.load(f'{current_path}/assets/images/player/{gun}/{animation}/{i}.png').convert_alpha()
                    img = pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
                    rotated_images = {
                        "up": pygame.transform.rotate(img, 90),
                        "down": pygame.transform.rotate(img, 270),
                        "left": pygame.transform.rotate(img, 180),
                        "right": img
                    }
                    temp_list.append(rotated_images)
                self.animation_dict[gun].append(temp_list)

    def switch_gun(self, gun):
        self.current_gun = gun

    def update_action(self, new_action):
        # If we're shooting, wait for animation to complete
        if self.action == 3 and not self.animation_completed:
            return
        if self.action == 2 and not self.animation_completed:
            return
     
        # Update action if it's different
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
            self.animation_completed = False
            self.isReloading = False
            
            # Reset c when starting a new action that's not shooting
            if new_action != 3:
                self.can_shoot = True

    def move(self, direction, walls):
        
        new_x, new_y = self.x, self.y
        is_moving = False

        if direction == "up":
            new_y -= PLAYER_SPEED
            self.direction = "up"
            is_moving = True

        elif direction == "down":
            new_y += PLAYER_SPEED
            self.direction = "down"
            is_moving = True

        elif direction == "left":
            new_x -= PLAYER_SPEED
            self.direction = "left"
            is_moving = True

        elif direction == "right":
            new_x += PLAYER_SPEED
            self.direction = "right"
            is_moving = True

        # Update animation state based on movement
        if is_moving:
            self.update_action(1)  # Move animation
            if not self.is_Walking_Sound:
                walk_sound.play(-1)  # Play walking sound
                self.is_Walking_Sound = True
        else:
            self.update_action(0)  # Idle animation
            if self.is_Walking_Sound:
                walk_sound.stop()  # Stop walking sound
                self.is_Walking_Sound = False

        # Wall collision check
        for wall in walls:
            if (new_x + PLAYER_SIZE > wall[0].x and new_x < wall[0].x + CELL_SIZE_SCALED and
                new_y + PLAYER_SIZE > wall[0].y and new_y < wall[0].y + CELL_SIZE_SCALED):

                # Stop walking sound if colliding with wall
                if self.is_Walking_Sound:
                    walk_sound.stop()
                    self.is_Walking_Sound = False

                if direction in ["up", "down"]:
                    new_y = self.y
                if direction in ["left", "right"]:
                    new_x = self.x

        self.x, self.y = new_x, new_y
        self.rect.topleft = (self.x, self.y)


    def shoot(self):
        
        if gun_info[self.current_gun]["remaining_ammo"] <= 0 and pygame.time.get_ticks() - self.animation_cool_down > 500:
            pygame.mixer.Sound(str(current_path) +'/assets/sound_effect/gun_sound/empty_gun.mp3').play()
            self.animation_cool_down = pygame.time.get_ticks()
            return
        if self.can_shoot and not self.isReloading and gun_info[self.current_gun]["remaining_ammo"] > 0:
            self.can_shoot = False  # Prevent shooting until animation completes
            if pygame.time.get_ticks() - self.animation_cool_down > gun_info[self.current_gun]["cooldown"]:
                self.update_action(3)  # Shoot animation
                self.animation_cool_down = pygame.time.get_ticks()
                pygame.mixer.Sound(gun_info[self.current_gun]['sound']).play()


                # Calculate bullet direction
                dx, dy = 0, 0
                if self.direction == "up":
                    dx, dy = 0, -1
                elif self.direction == "down":
                    dx, dy = 0, 1
                elif self.direction == "left":
                    dx, dy = -1, 0
                elif self.direction == "right":
                    dx, dy = 1, 0

                if self.current_gun == "shotgun":
                    # Fire multiple bullets with spread
                    for _ in range(BULLET_COUNT):
                        spread_angle = random.uniform(-BULLET_SPREAD / 2, BULLET_SPREAD / 2)
                        angle = math.atan2(dy, dx) + math.radians(spread_angle)
                        bullet_dx = math.cos(angle) * BULLET_SPEED
                        bullet_dy = math.sin(angle) * BULLET_SPEED
                        bullet = {
                            "x": self.x + PLAYER_SIZE // 2,
                            "y": self.y + PLAYER_SIZE // 2,
                            "dx": bullet_dx,
                            "dy": bullet_dy
                        }
                        self.bullets.append(bullet)
                else:
                    # Fire a single bullet
                    bullet = {
                        "x": self.x + PLAYER_SIZE // 2,
                        "y": self.y + PLAYER_SIZE // 2,
                        "dx": dx * BULLET_SPEED * 2,
                        "dy": dy * BULLET_SPEED * 2
                    }
                    self.bullets.append(bullet)

                gun_info[self.current_gun]['remaining_ammo'] -= 1



    def reload(self):
        if (gun_info[self.current_gun]['remaining_ammo'] == gun_info[self.current_gun]['magazine']  or self.isReloading or gun_info[self.current_gun]['ammo'] <= 0):
            return
        self.update_action(2)  # Reload animation
        pygame.mixer.Sound(gun_info[self.current_gun]['reloading_sound']).play()
        self.isReloading = True  # Prevent actions while reloading
        self.can_shoot = False  # Prevent shooting during reload
        
        # Simulate reload delay
        if pygame.time.get_ticks() - self.animation_cool_down > 200:
            self.animation_cool_down = pygame.time.get_ticks()
            
            bullets_to_reload = gun_info[self.current_gun]['magazine'] - gun_info[self.current_gun]["remaining_ammo"]
            
            if gun_info[self.current_gun]['ammo'] < bullets_to_reload:
                gun_info[self.current_gun]["remaining_ammo"] = gun_info[self.current_gun]['ammo']
                bullets_to_reload = gun_info[self.current_gun]['ammo']
            else:      
                gun_info[self.current_gun]["remaining_ammo"] = gun_info[self.current_gun]["magazine"]

            gun_info[self.current_gun]['ammo'] -= bullets_to_reload
            

            self.can_shoot = True
            


    def update_bullets(self, walls, zombies, dead_zombie_list):
        bullets_to_remove = []
        for bullet in self.bullets:
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]

            # Check for collisions with walls
            for wall, wall_type in walls:
                if (bullet["x"] > wall.x and bullet["x"] < wall.x + CELL_SIZE_SCALED and
                    bullet["y"] > wall.y and bullet["y"] < wall.y + CELL_SIZE_SCALED):
                    bullets_to_remove.append(bullet)
                    if wall_type == "breakable":
                        isbreak = wall.take_damage(gun_info[self.current_gun]['damage'])  # Reduce wall health
                        if isbreak:
                            walls.remove((wall, wall_type))
                    break

            # Check for collisions with zombies
            for zombie in zombies[:]:
                if (bullet["x"] > zombie.x and bullet["x"] < zombie.x + ZOMBIE_SIZE and
                    bullet["y"] > zombie.y and bullet["y"] < zombie.y + ZOMBIE_SIZE):
                    zombie.health -= gun_info[self.current_gun]['damage']  # Reduce zombie health
                    if zombie.health <= 0:
                        
                        dead_zombie_list.append(zombie)
                        # Play a random zombie death sound
                        random_sound = ['zombie_die1', 'zombie_die2', 'zombie_die3']
                        sound = random.choice(random_sound)
                        sound = str(current_path) +"/assets/sound_effect/zombie_die/" + sound + ".mp3"
                        pygame.mixer.Sound(sound).play()
                        zombies.remove(zombie)  # Remove the zombie
                    bullets_to_remove.append(bullet)  # Remove the bullet
                    break

        # Remove bullets marked for removal
        for bullet in bullets_to_remove:
            self.bullets.remove(bullet)


    def update_animation(self):

        # Update image depending on current gun, action, and frame
        self.image = self.animation_dict[self.current_gun][self.action][self.frame_index][self.direction]

        # Check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            # If the animation has run out
            if self.frame_index >= len(self.animation_dict[self.current_gun][self.action]):
                self.frame_index = 0
                # Mark animation as completed
                self.animation_completed = True
                self.can_shoot = True  # Reset shooting ability when animation completes
                # Return to idle if we were shooting
                if self.action == 3:  # Shooting
                    self.action = 0  # Return to idle


    def draw(self, screen, camera=None):
        if not self.alive:
            walk_sound.stop()
        screen.blit(self.image, camera.apply(self))  # Apply camera offset and draw