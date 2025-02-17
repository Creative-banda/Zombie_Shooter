import pygame
import pathlib, math, os, random
from extra.zombie_settings import CELL_SIZE_SCALED, ZOMBIE_SIZE, ZOMBIE_SPEED, PLAYER_SIZE, scale_x, IMAGES_DIR, SOUNDS_DIR

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
        self.animation_list = []
        self.action = 1  # 0: move, 1: idle, 2: attack
        self.last_hit_time = pygame.time.get_ticks()
        self.isPlayerSeen = False
        self.seen_audio = False


        # Animation list
        animation_types = ["move","idle","attack"]

        # look for how many images is in the directory
        for animation in animation_types:
         # Load animation frames
            temp_list = []
            num_of_frames = len(os.listdir(f'{IMAGES_DIR}/zombie/{animation}'))
            for i in range(num_of_frames):  
                img_path = f'{IMAGES_DIR}/zombie/{animation}/skeleton-{animation}_{i}.png' 
                image = pygame.image.load(img_path).convert_alpha()
                # Scale the image
                image = pygame.transform.scale(image, (ZOMBIE_SIZE, ZOMBIE_SIZE))
                temp_list.append(image)
            self.animation_list.append(temp_list)

        # Current image to display
        self.image = self.animation_list[self.action][self.frame_index]
        self.direction = "down"  # Default direction

        # Add a rect attribute for collision and rendering
        self.rect = pygame.Rect(self.x, self.y, ZOMBIE_SIZE, ZOMBIE_SIZE)

    def move_towards_player(self, player, walls):
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        if (self.can_see_player(player, walls) or self.isPlayerSeen) and distance < 200 * scale_x:  # Check if the zombie can see the player
        
            if distance > 10: # Move only if the player is far enough
                    
                self.update_animation(0)  # Update the zombie's animation to move
                dx = dx / distance * ZOMBIE_SPEED
                dy = dy / distance * ZOMBIE_SPEED
                
                # Try direct movement first
                new_x = self.x + dx
                new_y = self.y + dy
                
                # Check collision with walls
                direct_path_blocked = False
                for wall, _ in walls:  # Unpack the tuple into wall and _ (no need for the second element   )
                    if (new_x + ZOMBIE_SIZE > wall.x and        
                        new_x < wall.x + CELL_SIZE_SCALED and
                        new_y + ZOMBIE_SIZE > wall.y and 
                        new_y < wall.y + CELL_SIZE_SCALED):
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
                    
                    for wall,_ in walls:
                        if (new_x + ZOMBIE_SIZE > wall.x and 
                            new_x < wall.x + CELL_SIZE_SCALED and
                            new_y + ZOMBIE_SIZE > wall.y and 
                            new_y < wall.y + CELL_SIZE_SCALED):
                            can_move_horizontal = False
                            break
                    
                    # Try vertical movement only
                    if not can_move_horizontal:
                        new_x = self.x
                        new_y = self.y + dy
                        can_move_vertical = True
                        
                        for wall,_ in walls:
                            if (new_x + ZOMBIE_SIZE > wall.x and 
                                new_x < wall.x + CELL_SIZE_SCALED and
                                new_y + ZOMBIE_SIZE > wall.y and 
                                new_y < wall.y + CELL_SIZE_SCALED):
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

        # Rotate the current frame based on direction
        if self.direction == "right":
            self.image = pygame.transform.rotate(self.animation_list[self.action][self.frame_index], 270)
        elif self.direction == "left":
            self.image = pygame.transform.rotate(self.animation_list[self.action][self.frame_index], 90)
        elif self.direction == "down":
            self.image = pygame.transform.rotate(self.animation_list[self.action][self.frame_index], 180)
        elif self.direction == "up":
            self.image = self.animation_list[self.action][self.frame_index]  # No rotation for up

    def draw(self, screen, camera=None):
        # Update the rect position to match the zombie's current position
        self.rect.topleft = (self.x, self.y)
        
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering

    def check_for_player(self, player):
        # Check for zombie collision with player
        if (self.x < player.x + PLAYER_SIZE and self.x + ZOMBIE_SIZE > player.x and
            self.y < player.y + PLAYER_SIZE and self.y + ZOMBIE_SIZE > player.y):
            if player.health > 0:
                self.update_animation(2)  # Update the zombie's animation to attack
                # Play the random damage sound effect
                if pygame.time.get_ticks() - self.last_hit_time > 1000:  # Limit the sound effect to play every 1 second
                    music = random.choice(['1', '2', '3', '4', '5'])
                    sound = f"{SOUNDS_DIR / 'damage_sound'}/{music}.mp3"
                    pygame.mixer.Sound(sound).play()
                    player.health -= 20  # Reduce player health on collision
                    self.last_hit_time = pygame.time.get_ticks()

        
    def update_animation(self, new_action):
        if new_action == self.action:
            return
        
        # Update the animation settings
        self.action = new_action
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
    

    def can_see_player(self, player, walls, vision_angle=160):
        """
        Check if the zombie can see the player within a specific angle range.

        :param player: Player object containing x and y attributes
        :param walls: List of tuples containing Wall objects and wall types
        :param vision_angle: The vision angle (in degrees) within which the zombie can see
        :return: True if the zombie can see the player, False otherwise
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
        for wall, _ in walls:  # Extract wall object and type (ignore type here)
            if wall.rect.clipline(line):  # If the line intersects with a wall
                return False  # Zombie cannot see the player

        # If no walls block the line of sight, the zombie can see the player
        if not self.seen_audio and random.choice([True, False]):
            pygame.mixer.Sound(f"{SOUNDS_DIR / 'zombie_see_1'}.mp3").play()
            pygame.mixer.Sound(f"{SOUNDS_DIR / 'alert'}.mp3").play()

            self.seen_audio = True

        self.isPlayerSeen = True

        return True
