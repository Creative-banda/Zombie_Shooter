import pygame
import pathlib, math, os, random
from extra.zombie_settings import CELL_SIZE_SCALED, ZOMBIE_SIZE, ZOMBIE_SPEED, PLAYER_SIZE, scale_x, IMAGES_DIR, SOUNDS_DIR, BASE_FPS, ZOMBIE_ANIMATIONS, SOUND_EFFECTS

# Constants
ANIMATION_COOLDOWN = 100 

current_path = pathlib.Path().absolute()


class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 100
        self.frame_index = 0 
        self.update_time = pygame.time.get_ticks()
        self.action = 1  # 0: move, 1: idle, 2: attack
        self.last_hit_time = pygame.time.get_ticks()
        self.isPlayerSeen = False
        self.seen_audio = False

        # Current image to display
        self.direction = "down"  # Default direction
        # Use pre-loaded animation list (0: move, 1: idle, 2: attack)
        self.animation_list = [ZOMBIE_ANIMATIONS[0], ZOMBIE_ANIMATIONS[1], ZOMBIE_ANIMATIONS[2]]
        self.image = self.animation_list[self.action][self.frame_index][self.direction]

        # Add a rect attribute for collision and rendering
        self.rect = pygame.Rect(self.x, self.y, ZOMBIE_SIZE, ZOMBIE_SIZE)

    def move_towards_player(self, player, walls, dt, los_walls=None):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        if (self.can_see_player(player, walls, los_walls=los_walls) or self.isPlayerSeen) and distance < 200 * scale_x:  # Check if the zombie can see the player
        
            if distance > 10: # Move only if the player is far enough
                    
                self.update_animation(0)  # Update the zombie's animation to move
                speed = ZOMBIE_SPEED * dt * BASE_FPS
                dx = dx / distance * speed
                dy = dy / distance * speed
                
                # Try direct movement first
                new_x = self.x + dx
                new_y = self.y + dy
                
                # Check collision with walls using rect.colliderect
                direct_path_blocked = False
                temp_rect = pygame.Rect(new_x, new_y, ZOMBIE_SIZE, ZOMBIE_SIZE)
                for wall, _ in walls:
                    if temp_rect.colliderect(wall.rect):
                        direct_path_blocked = True
                        break
                
                if direct_path_blocked:
                    # Try horizontal movement only
                    new_x = self.x + dx
                    new_y = self.y
                    temp_rect.topleft = (new_x, new_y)
                    can_move_horizontal = True
                    
                    for wall,_ in walls:
                        if temp_rect.colliderect(wall.rect):
                            can_move_horizontal = False
                            break
                    
                    # Try vertical movement only
                    if not can_move_horizontal:
                        new_x = self.x
                        new_y = self.y + dy
                        temp_rect.topleft = (new_x, new_y)
                        can_move_vertical = True
                        
                        for wall,_ in walls:
                            if temp_rect.colliderect(wall.rect):
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

        else:
            # If the zombie cannot see the player, stop moving
            self.update_animation(1)  # Update the zombie's animation to idle

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
            if self.frame_index >= len(self.animation_list[self.action]):
                self.frame_index = 0

        # Pick pre-rotated frame based on direction
        self.image = self.animation_list[self.action][self.frame_index][self.direction]

    def draw(self, screen, camera=None):
        # Update the rect position to match the zombie's current position
        self.rect.topleft = (self.x, self.y)
        
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering

    def check_for_player(self, player):
        # Check for zombie collision with player using rect.colliderect
        if self.rect.colliderect(player.rect):
            if player.health > 0:
                self.update_animation(2)  # Update the zombie's animation to attack
                # Play the random damage sound effect from pre-loaded registry
                if pygame.time.get_ticks() - self.last_hit_time > 1000:
                    random.choice(SOUND_EFFECTS["damage"]).play()
                    player.health -= 20  # Reduce player health on collision
                    self.last_hit_time = pygame.time.get_ticks()

        
    def update_animation(self, new_action):
        if new_action == self.action:
            return
        
        # Update the animation settings
        self.action = new_action
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
    

    def can_see_player(self, player, walls, vision_angle=160, los_walls=None):
        """
        Check if the zombie can see the player within a specific angle range.
        """
        # Calculate the direction vector from the zombie to the player
        dx = player.x - self.x
        dy = player.y - self.y
        angle_to_player = math.degrees(math.atan2(dy, dx))  # Angle from zombie to player

        # Assuming the zombie's facing direction is a fixed angle (e.g., 0 degrees)
        zombie_facing_angle = 90  # Replace this with the actual facing direction of the zombie

        # Calculate the absolute difference between the angles
        angle_difference = abs((angle_to_player - zombie_facing_angle + 180) % 360 - 180)

        # Check if the player is within the vision angle
        if angle_difference > vision_angle / 2:
            return False  # Player is outside the vision angle

        # Create a line from zombie to player
        line = ((self.x, self.y), (player.x, player.y))

        # Check for walls blocking the line of sight
        wall_candidates = los_walls if los_walls is not None else walls
        for wall, _ in wall_candidates:
            if wall.rect.clipline(line):  # If the line intersects with a wall
                return False  # Zombie cannot see the player

        # If no walls block the line of sight, the zombie can see the player
        if not self.seen_audio and random.choice([True, False]):
            SOUND_EFFECTS["zombie_see"].play()
            SOUND_EFFECTS["alert"].play()
            self.seen_audio = True

        self.isPlayerSeen = True
        return True
