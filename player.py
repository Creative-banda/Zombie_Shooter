import pygame
import random
import os

PLAYER_SIZE = 40
CELL_SIZE = 40

pygame.mixer.init()

shoot_sound = pygame.mixer.Sound('assets/sound_effect/shoot.wav')



BULLET_DAMAGE = 50  # Damage per bullet
BULLET_SIZE = 2  # Bullet size
ZOMBIE_SIZE = 30


class Player:
    def __init__(self, WINDOW_WIDTH, WINDOW_HEIGHT):
        self.alive = True
        self.direction = "right"
        self.animation_cool_down = pygame.time.get_ticks()
        self.update_time = pygame.time.get_ticks()
        
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT // 2
        self.rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)

        # Animation states
        self.animation_list = []
        self.frame_index = 0
        self.action = 0  # 0: idle, 1: move, 2: reload, 3: shoot
        self.last_action = 0
        self.animation_completed = True
        
        self.speed = 2
        self.ammo = 100
        self.health = 100
        self.bullets = []

        # Load animations
        animation_types = ['idle', 'move', 'reload', 'shoot']
        for animation in animation_types:
            temp_list = []
            num_of_frames = len(os.listdir(f'assets/images/player/handgun/{animation}'))
            for i in range(num_of_frames):
                img = pygame.image.load(f'assets/images/player/handgun/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
                rotated_images = {
                    "up": pygame.transform.rotate(img, 90),
                    "down": pygame.transform.rotate(img, 270),
                    "left": pygame.transform.rotate(img, 180),
                    "right": img
                }
                temp_list.append(rotated_images)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index][self.direction]

    def update_action(self, new_action):
        # If we're shooting, wait for animation to complete
        if self.action == 3 and not self.animation_completed:
            return
            
        # Update action if it's different
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
            self.animation_completed = False
            
            # Reset can_shoot when starting a new action that's not shooting
            if new_action != 3:
                self.can_shoot = True

    def move(self, walls):
        keys = pygame.key.get_pressed()
        new_x, new_y = self.x, self.y
        is_moving = False

        if keys[pygame.K_w]:
            new_y -= self.speed
            self.direction = "up"
            is_moving = True
        elif keys[pygame.K_s]:
            new_y += self.speed
            self.direction = "down"
            is_moving = True
        elif keys[pygame.K_a]:
            new_x -= self.speed
            self.direction = "left"
            is_moving = True
        elif keys[pygame.K_d]:
            new_x += self.speed
            self.direction = "right"
            is_moving = True

        # Update animation state based on movement
        if is_moving:
            self.update_action(1)  # Move animation
        else:
            self.update_action(0)  # Idle animation

        # Wall collision check
        for wall in walls:
            if (new_x + PLAYER_SIZE > wall[0].x and new_x < wall[0].x + CELL_SIZE and
                new_y + PLAYER_SIZE > wall[0].y and new_y < wall[0].y + CELL_SIZE):
                if keys[pygame.K_w] or keys[pygame.K_s]:
                    new_y = self.y
                if keys[pygame.K_a] or keys[pygame.K_d]:
                    new_x = self.x

        self.x, self.y = new_x, new_y
        self.rect.topleft = (self.x, self.y)


    def shoot(self):
        if self.ammo > 0 and self.can_shoot:
            self.update_action(3)  # Shoot animation
            self.can_shoot = False  # Prevent shooting until animation completes
            
            if pygame.time.get_ticks() - self.animation_cool_down > 200:
                self.animation_cool_down = pygame.time.get_ticks()
                shoot_sound.play()
                
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

                bullet = {
                    "x": self.x + PLAYER_SIZE // 2,
                    "y": self.y + PLAYER_SIZE // 2,
                    "dx": dx * 10,
                    "dy": dy * 10
                }
                self.bullets.append(bullet)
                self.ammo -= 1

    def update_bullets(self, walls, zombies):
        bullets_to_remove = []
        for bullet in self.bullets:
            bullet["x"] += bullet["dx"]
            bullet["y"] += bullet["dy"]

            # Check for collisions with walls
            for wall, wall_type in walls:
                if (bullet["x"] > wall.x and bullet["x"] < wall.x + CELL_SIZE and
                    bullet["y"] > wall.y and bullet["y"] < wall.y + CELL_SIZE):
                    bullets_to_remove.append(bullet)
                    if wall_type == "breakable":
                        isbreak = wall.take_damage(BULLET_DAMAGE)  # Reduce wall health
                        if isbreak:
                            walls.remove((wall, wall_type))
                    break

            # Check for collisions with zombies
            for zombie in zombies[:]:
                if (bullet["x"] > zombie.x and bullet["x"] < zombie.x + ZOMBIE_SIZE and
                    bullet["y"] > zombie.y and bullet["y"] < zombie.y + ZOMBIE_SIZE):
                    zombie.health -= BULLET_DAMAGE  # Reduce zombie health
                    if zombie.health <= 0:
                        # Play a random zombie death sound
                        random_sound = ['zombie_die1', 'zombie_die2', 'zombie_die3']
                        sound = random.choice(random_sound)
                        sound = "assets/sound_effect/zombie_die/" + sound + ".mp3"
                        pygame.mixer.Sound(sound).play()
                        zombies.remove(zombie)  # Remove the zombie
                    bullets_to_remove.append(bullet)  # Remove the bullet
                    break

        # Remove bullets marked for removal
        for bullet in bullets_to_remove:
            self.bullets.remove(bullet)


    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        
        # Update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index][self.direction]
        
        # Check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
            
            # If the animation has run out
            if self.frame_index >= len(self.animation_list[self.action]):
                self.frame_index = 0
                # Mark animation as completed
                self.animation_completed = True
                self.can_shoot = True  # Reset shooting ability when animation completes
                # Return to idle if we were shooting
                if self.action == 3:  # Shooting
                    self.action = 0  # Return to idle

    def draw(self, screen, camera=None):
        screen.blit(self.image, camera.apply(self))  # Apply camera offset

        