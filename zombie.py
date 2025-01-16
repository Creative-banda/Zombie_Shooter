import pygame
import pathlib
import math

ZOMBIE_SIZE = 30
CELL_SIZE = 40
ANIMATION_COOLDOWN = 100 

current_path = pathlib.Path().absolute()


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
            img_path = str(current_path) +'/assets/images/zombie/', f'{i+1}.png' 
            img_path = ''.join(img_path)

            image = pygame.image.load(img_path).convert_alpha()
            # Scale the image
            image = pygame.transform.scale(image, (ZOMBIE_SIZE, ZOMBIE_SIZE))
            self.animation_list.append(image)

        # Current image to display
        self.image = self.animation_list[self.frame_index]
        self.direction = "down"  # Default direction

        # Add a rect attribute for collision and rendering
        self.rect = pygame.Rect(self.x, self.y, ZOMBIE_SIZE, ZOMBIE_SIZE)

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
            for wall, wall_type in walls:  # Unpack the tuple into wall and wall_type
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
                
                for wall,_ in walls:
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
                    
                    for wall,_ in walls:
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

    def draw(self, screen, camera=None):
        # Update the rect position to match the zombie's current position
        self.rect.topleft = (self.x, self.y)
        
        if camera:
            screen.blit(self.image, camera.apply(self))  # Apply camera offset
        else:
            screen.blit(self.image, (self.x, self.y))  # Default rendering

