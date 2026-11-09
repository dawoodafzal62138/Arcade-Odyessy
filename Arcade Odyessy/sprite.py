import random
import math
import pygame
from settigns import *


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups,):
        # Support both (pos, surface, groups) and (surface, pos, groups)
        if isinstance(pos, pygame.Surface):
            surface, pos = pos, surface
       
        super().__init__(groups)
        self.image = surface
        if hasattr(self.image, 'get_frect'):
            self.rect = self.image.get_frect(topleft=pos)
        else:
            self.rect = self.image.get_rect(topleft=pos)


class CollisionSprites(pygame.sprite.Sprite):
    def __init__(self, pos, surface_or_size, groups):
        # Support both (pos, surface_or_size, groups) and (surface_or_size, pos, groups)
        if isinstance(pos, pygame.Surface):
            surface_or_size, pos = pos, surface_or_size
        super().__init__(groups)
        if isinstance(surface_or_size, pygame.Surface):
            self.image = surface_or_size
        else:
            self.image = pygame.Surface(surface_or_size, pygame.SRCALPHA)
        if hasattr(self.image, 'get_frect'):
            self.rect = self.image.get_frect(topleft=pos)
        else:
            self.rect = self.image.get_rect(topleft=pos)


class Animation(Sprite):
    def __init__(self, pos, frames, groups, z=0):
        self.frames = frames
        self.frame_index = 0
        self.animation_speed = 10
        if isinstance(frames, dict):
            first_key = 'idle' if 'idle' in frames else next(iter(frames))
            first_frame = frames[first_key][0]
        elif isinstance(frames, (list, tuple)):
            first_frame = frames[0]
        else:
            first_frame = frames
        super().__init__(pos, first_frame, groups)

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        if isinstance(self.frames, list):
            self.image = self.frames[int(self.frame_index) % len(self.frames)]


class JumpSpark(Sprite):
    """A short, fading magic spark emitted beneath an airborne wizard."""

    def __init__(self, pos, velocity, groups):
        super().__init__(pos, pygame.Surface((18, 18), pygame.SRCALPHA), groups)
        self.position = pygame.Vector2(pos)
        self.velocity = pygame.Vector2(velocity)
        self.lifetime = random.uniform(0.25, 0.45)
        self.remaining = self.lifetime

    def update(self, dt):
        self.remaining -= dt
        if self.remaining <= 0:
            self.kill()
            return
        self.position += self.velocity * dt
        self.velocity.y += 220 * dt
        self.rect.center = self.position
        self.image.fill((0, 0, 0, 0))
        radius = max(1, round(6 * self.remaining / self.lifetime))
        pygame.draw.circle(self.image, (65, 175, 255, 90), (9, 9), radius + 3)
        pygame.draw.circle(self.image, (175, 245, 255), (9, 9), radius)
        self.image.set_alpha(round(255 * self.remaining / self.lifetime))


class Player(Animation):
    def __init__(self, pos, groups, collisions_sprites, frames, create_bullet_func=None):
        super().__init__(pos, frames, groups)
      

        # Scaled collision box and image rect
        self.col_w = int(200 * PLAYER_SCALE)
        self.col_h = int(350 * PLAYER_SCALE)
        self.offset_x = int(156 * PLAYER_SCALE)
        self.offset_y = int(51 * PLAYER_SCALE)
        img_w = int(512 * PLAYER_SCALE)
        img_h = int(512 * PLAYER_SCALE)

        if hasattr(pygame, 'FRect'):
            self.rect = pygame.FRect(pos[0], pos[1], self.col_w, self.col_h)
            self.image_rect = pygame.FRect(self.rect.x - self.offset_x, self.rect.y - self.offset_y, img_w, img_h)
        else:
            self.rect = pygame.Rect(pos[0], pos[1], self.col_w, self.col_h)
            self.image_rect = pygame.Rect(self.rect.x - self.offset_x, self.rect.y - self.offset_y, img_w, img_h)

        self.collisions_sprites = collisions_sprites
        self.create_bullet = create_bullet_func

        # Movement and physics attributes matching Platform structure
        self.direction = pygame.Vector2()
        self.speed = 320
        self.gravity = 45
        self.on_floor = False
        self.flip = False
        self.state = 'idle'
        self.air_jump_available = True
        self.jump_held = False

    def jump(self):
        if self.on_floor:
            self.air_jump_available = True
        else:
            # Unlimited airborne jumps while testing the overworld.
            self.double_jump_effect()
        self.direction.y = -22
        self.on_floor = False
        self.frame_index = 0

    def double_jump_effect(self):
        for index in range(16):
            angle = math.tau * index / 16
            velocity = (math.cos(angle) * random.uniform(100, 190),
                        math.sin(angle) * 65 + 45)
            spark = JumpSpark(self.rect.midbottom, velocity, self.groups())
            for group in self.groups():
                if isinstance(group, pygame.sprite.LayeredUpdates):
                    group.change_layer(spark, group.get_layer_of_sprite(self) + 1)

    def input(self):
        key = pygame.key.get_pressed()
        self.direction.x = int(key[pygame.K_d]) - int(key[pygame.K_a]) or int(key[pygame.K_RIGHT]) - int(key[pygame.K_LEFT])
        jump_pressed = bool(key[pygame.K_w] or key[pygame.K_UP] or key[pygame.K_SPACE])
        if jump_pressed and not self.jump_held:
            self.jump()
        self.jump_held = jump_pressed

    def move(self, dt):
        # Horizontal movement & collision
        self.rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')

        # Vertical movement (gravity) & collision
        self.direction.y += self.gravity * dt
        self.rect.y += self.direction.y
        self.collision('vertical')

    def update(self, dt):
        self.check_on_floor()
        if self.on_floor and self.direction.y >= 0:
            self.air_jump_available = True
        self.input()
        self.move(dt)
        self.animate(dt)
        self.image_rect.topleft = (self.rect.x - self.offset_x, self.rect.y - self.offset_y)

    def animate(self, dt):
        # State determination
        if not self.on_floor:
            new_state = 'jump'
        elif self.direction.x != 0:
            new_state = 'walk'
            self.flip = self.direction.x < 0
        else:
            new_state = 'idle'

        # Reset animation index when switching states
        if new_state != self.state:
            self.state = new_state
            self.frame_index = 0

        self.frame_index += self.animation_speed * dt

        # Frame selection preserving scaled frame dimensions
        if isinstance(self.frames, dict):
            current_frames = self.frames.get(self.state, self.frames.get('idle', []))
            if current_frames:
                self.image = current_frames[int(self.frame_index) % len(current_frames)]
        elif isinstance(self.frames, list):
            if self.direction.x == 0:
                self.frame_index = 0
            elif self.direction.x:
                self.flip = self.direction.x < 0

            if not self.on_floor and len(self.frames) > 1:
                self.frame_index = 1

            self.image = self.frames[int(self.frame_index) % len(self.frames)]

        # Direction flip
        self.image = pygame.transform.flip(self.image, self.flip, False)

        # Enforce collision box for every frame
        self.rect.size = (self.col_w, self.col_h)
        self.image_rect.topleft = (self.rect.x - self.offset_x, self.rect.y - self.offset_y)

    def check_on_floor(self):
        if hasattr(pygame, 'FRect'):
            floor_rect = pygame.FRect((0, 0), (self.rect.width, 2))
            if hasattr(floor_rect, 'move_to'):
                bottom_rect = floor_rect.move_to(midtop=self.rect.midbottom)
            else:
                floor_rect.midtop = self.rect.midbottom
                bottom_rect = floor_rect
        else:
            bottom_rect = pygame.Rect(0, 0, int(self.rect.width), 2)
            bottom_rect.midtop = self.rect.midbottom

        self.on_floor = self.direction.y >= 0 and bottom_rect.collidelist([sprite.rect for sprite in self.collisions_sprites]) != -1

    def collision(self, direction):
        for sprite in self.collisions_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:  # moving right
                        self.rect.right = sprite.rect.left
                    if self.direction.x < 0:  # moving left
                        self.rect.left = sprite.rect.right
                if direction == 'vertical':
                    if self.direction.y > 0:  # moving down
                        self.rect.bottom = sprite.rect.top
                        self.direction.y = 0
                    if self.direction.y < 0:  # moving up
                        self.rect.top = sprite.rect.bottom
                        self.direction.y = 0
