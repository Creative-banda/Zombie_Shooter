import pygame
import random, copy
import os, math
from extra.zombie_settings import CELL_SIZE_SCALED, ZOMBIE_SIZE, PLAYER_SIZE, BULLET_SIZE, BULLET_SPEED, PLAYER_SPEED, walk_sound, IMAGES_DIR, SOUNDS_DIR, BASE_FPS, PLAYER_ANIMATIONS, SOUND_EFFECTS


print("Player Class Loaded")

pygame.mixer.init()


ANIMATION_COOLDOWN = 100

# Shotgun settings
BULLET_SPREAD = 45  # Degrees of spread
BULLET_COUNT = 6  # Number of bullets per shotgun shot


class Player():
    
    def __init__(self, WINDOW_WIDTH, WINDOW_HEIGHT, gun_info):
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
        # Create an independent copy of gun info, but keep shared sound objects
        self.gun_info = {k: v.copy() for k, v in gun_info.items()}

        # Animation properties
        self.frame_index = 0
        self.action = 0  # 0: idle, 1: move, 2: reload, 3: shoot
        self.animation_completed = True

        self.health = 100
        self.bullets = []
        self.current_gun = "handgun"  # Default gun
        self.isShotgun = True
        self.isRifle = True

        # Use pre-loaded animation dictionary
        self.animation_dict = PLAYER_ANIMATIONS
        self.image = self.animation_dict[self.current_gun][self.action][self.frame_index][self.direction]

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

    def move(self, walls, dt):
        keys = pygame.key.get_pressed()
        new_x, new_y = self.x, self.y
        is_moving = False

        move_speed = PLAYER_SPEED * dt * BASE_FPS

        if keys[pygame.K_w]:
            new_y -= move_speed
            self.direction = "up"
            is_moving = True
                
        elif keys[pygame.K_s]:
            new_y += move_speed
            self.direction = "down"
            is_moving = True
                
        elif keys[pygame.K_a]:
            new_x -= move_speed
            self.direction = "left"
            is_moving = True
                
        elif keys[pygame.K_d]:
            new_x += move_speed
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

        # Wall collision check using Rect.colliderect
        temp_rect = pygame.Rect(new_x, new_y, PLAYER_SIZE, PLAYER_SIZE)
        for wall, _ in walls:
            if temp_rect.colliderect(wall.rect):
                # turn off the walking sound
                if self.is_Walking_Sound:
                    walk_sound.stop()
                    self.is_Walking_Sound = False

                if keys[pygame.K_w] or keys[pygame.K_s]:
                    new_y = self.y
                if keys[pygame.K_a] or keys[pygame.K_d]:
                    new_x = self.x
                break

        self.x, self.y = new_x, new_y
        self.rect.topleft = (self.x, self.y)

    def shoot(self):
        if self.gun_info[self.current_gun]["remaining_ammo"] <= 0 and pygame.time.get_ticks() - self.animation_cool_down > 500:
            SOUND_EFFECTS["empty_gun"].play()
            self.animation_cool_down = pygame.time.get_ticks()
            return

        if self.can_shoot and not self.isReloading and self.gun_info[self.current_gun]["remaining_ammo"] > 0:
            self.can_shoot = False  # Prevent shooting until animation completes
            if pygame.time.get_ticks() - self.animation_cool_down > self.gun_info[self.current_gun]["cooldown"]:
                self.update_action(3)  # Shoot animation
                self.animation_cool_down = pygame.time.get_ticks()
                self.gun_info[self.current_gun]['sound'].play()

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

                self.gun_info[self.current_gun]['remaining_ammo'] -= 1



    def reload(self):
        if (self.gun_info[self.current_gun]['remaining_ammo'] == self.gun_info[self.current_gun]['magazine']  or self.isReloading or self.gun_info[self.current_gun]['ammo'] <= 0):
            return
        self.update_action(2)  # Reload animation
        self.gun_info[self.current_gun]['reloading_sound'].play()
        self.isReloading = True  # Prevent actions while reloading
        self.can_shoot = False  # Prevent shooting during reload
        
        # Simulate reload delay
        if pygame.time.get_ticks() - self.animation_cool_down > 200:
            self.animation_cool_down = pygame.time.get_ticks()
            
            bullets_to_reload = self.gun_info[self.current_gun]['magazine'] - self.gun_info[self.current_gun]["remaining_ammo"]
            
            if self.gun_info[self.current_gun]['ammo'] < bullets_to_reload:
                self.gun_info[self.current_gun]["remaining_ammo"] = self.gun_info[self.current_gun]['ammo']
                bullets_to_reload = self.gun_info[self.current_gun]['ammo']
            else:      
                self.gun_info[self.current_gun]["remaining_ammo"] = self.gun_info[self.current_gun]["magazine"]

            self.gun_info[self.current_gun]['ammo'] -= bullets_to_reload
            

            self.can_shoot = True
            


    def update_bullets(self, walls, zombies, dead_zombie_list, dt, wall_grid=None, zombie_grid=None):
        bullets_to_remove = []
        step = dt * BASE_FPS

        # Reuse a single Rect for bullet collisions
        bullet_rect = pygame.Rect(0, 0, BULLET_SIZE * 2, BULLET_SIZE * 2)

        for bullet in self.bullets:
            bullet["x"] += bullet["dx"] * step
            bullet["y"] += bullet["dy"] * step

            # Update bullet_rect position
            bullet_rect.center = (int(bullet["x"]), int(bullet["y"]))

            # Check for collisions with walls
            walls_to_check = wall_grid.query_rect(bullet_rect) if wall_grid else walls
            for wall, wall_type in walls_to_check:
                if bullet_rect.colliderect(wall.rect):
                    bullets_to_remove.append(bullet)
                    if wall_type == "breakable":
                        isbreak = wall.take_damage(self.gun_info[self.current_gun]['damage'])  # Reduce wall health
                        if isbreak:
                            if wall_grid:
                                wall_grid.remove((wall, wall_type), wall.rect)
                            walls.remove((wall, wall_type))
                    break

            # Check for collisions with zombies
            if bullet in bullets_to_remove: continue

            zombies_to_check = zombie_grid.query_rect(bullet_rect) if zombie_grid else zombies
            for zombie in zombies_to_check:
                if bullet_rect.colliderect(zombie.rect):
                    zombie.health -= self.gun_info[self.current_gun]['damage']  # Reduce zombie health

                    # Activate the zombie if it's not already
                    if not zombie.isPlayerSeen:
                        zombie.isPlayerSeen = True

                    if zombie.health <= 0:
                        dead_zombie_list.append(zombie)
                        # Play a random zombie death sound from pre-loaded registry
                        random.choice(SOUND_EFFECTS["zombie_die"]).play()
                        if zombie_grid:
                            zombie_grid.remove(zombie, zombie.rect)
                        if zombie in zombies:
                            zombies.remove(zombie)  # Remove the zombie
                    bullets_to_remove.append(bullet)  # Remove the bullet
                    break

        # Remove bullets marked for removal
        for bullet in bullets_to_remove:
            try:
                self.bullets.remove(bullet)
            except ValueError:
                pass


    def update_animation(self):

        # Update image depending on current gun, action, and frame
        try:
            self.image = self.animation_dict[self.current_gun][self.action][self.frame_index][self.direction]
        except:
            pass

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
