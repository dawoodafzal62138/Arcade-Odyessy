import os
import sys
import math
import random
from pathlib import Path
import pygame
from pytmx.util_pygame import load_pygame
from settigns import WIDTH, HEIGHT, CURRENT_DIR


# =========================================================================
# PLATFORM GAME (Native 1280x720 resolution)
# Completely self-contained to avoid namespace collisions with Arcade Odyssey
# =========================================================================
PLATFORM_BASE = str((CURRENT_DIR.parent / "Platform").resolve())

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
TILE_SIZE = 64
FRAMERATE = 60
BG_COLOR = '#fcdfcd'


def import_image(path, alpha=True):
    return pygame.image.load(path).convert_alpha() if alpha else pygame.image.load(path).convert()


def import_folder(path):
    frames = []
    for image_name in sorted(os.listdir(path)):
        full_path = os.path.join(path, image_name)
        if os.path.isfile(full_path):
            frames.append(pygame.image.load(full_path).convert_alpha())
    return frames


class PlatformTimer:
    def __init__(self, duration, func=None, repeat=None, autostart=False):
        self.duration = duration
        self.func = func
        self.repeat = repeat
        self.start_time = 0
        self.active = False
        self.autostart = autostart
        if self.autostart:
            self.activate()

    def activate(self):
        self.active = True
        self.start_time = pygame.time.get_ticks()

    def deactivate(self):
        self.active = False
        self.start_time = 0
        if self.repeat:
            self.activate()

    def update(self):
        if self.active:
            if pygame.time.get_ticks() - self.start_time >= self.duration:
                if self.func and self.start_time != 0:
                    self.func()
                self.deactivate()

    def __bool__(self):
        return self.active


class PlatformSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surface, groups):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_frect(topleft=pos) if hasattr(self.image, 'get_frect') else self.image.get_rect(topleft=pos)


class PlatformAnimation(PlatformSprite):
    def __init__(self, pos, frames, groups):
        self.frames = frames
        self.frame_index = 0
        self.animation_speed = 10
        super().__init__(pos, frames[self.frame_index], groups)

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]


class PlatformBullet(PlatformSprite):
    def __init__(self, surf, pos, direction, groups):
        super().__init__(pos, surf, groups)
        self.direction = direction
        self.speed = 850

    def update(self, dt):
        self.rect.x += self.direction * self.speed * dt


class PlatformFire(PlatformSprite):
    def __init__(self, surf, pos, groups, player):
        super().__init__(pos, surf, groups)
        self.player = player
        self.flip = self.player.flip
        self.timer = PlatformTimer(100, autostart=True, func=self.kill)
        self.y_offset = pygame.Vector2(0, 8)

        if self.flip:
            self.rect.midright = self.player.rect.midleft + self.y_offset
            self.image = pygame.transform.flip(self.image, True, False)
        else:
            self.rect.midleft = self.player.rect.midright + self.y_offset

    def update(self, _):
        self.timer.update()
        if self.flip:
            self.rect.midright = self.player.rect.midleft + self.y_offset
        else:
            self.rect.midleft = self.player.rect.midright + self.y_offset
        if self.flip != self.player.flip:
            self.kill()


class PlatformPlayer(PlatformAnimation):
    def __init__(self, pos, groups, collisions_sprites, frames, create_bullet_func):
        super().__init__(pos, frames, groups)
        self.collisions_sprites = collisions_sprites
        self.create_bullet = create_bullet_func

        self.direction = pygame.Vector2()
        self.speed = 400
        self.gravity = 50
        self.on_floor = False
        self.flip = False

        self.timer = PlatformTimer(500)
        self.death_timer = PlatformTimer(1000, func=self.kill)

    def destroy(self):
        self.death_timer.activate()
        self.animation_speed = 0
        self.image = pygame.mask.from_surface(self.image).to_surface()
        self.image.set_colorkey("black")

    def input(self):
        key = pygame.key.get_pressed()
        self.direction.x = int(key[pygame.K_d]) - int(key[pygame.K_a]) or int(key[pygame.K_RIGHT]) - int(key[pygame.K_LEFT])
        if (key[pygame.K_w] or key[pygame.K_UP]) and self.on_floor:
            self.direction.y = -20

        if key[pygame.K_SPACE] and not self.timer.active:
            self.create_bullet(self.rect.center, 1 if not self.flip else -1)
            self.timer.activate()

    def move(self, dt):
        self.rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')

        self.direction.y += self.gravity * dt
        self.rect.y += self.direction.y
        self.collision('vertical')

    def update(self, dt):
        self.check_on_floor()
        self.timer.update()
        self.death_timer.update()
        if not self.death_timer:
            self.input()
            self.move(dt)
            self.animate(dt)

    def animate(self, dt):
        if self.direction.x == 0:
            self.frame_index = 0
        elif self.direction.x:
            self.frame_index += self.animation_speed * dt
            self.flip = self.direction.x < 0

        if not self.on_floor:
            self.frame_index = 1

        self.image = self.frames[int(self.frame_index) % len(self.frames)]
        self.image = pygame.transform.flip(self.image, self.flip, False)

    def check_on_floor(self):
        if hasattr(pygame, 'FRect'):
            bottom_rect = pygame.FRect((0, 0), (self.rect.width, 2)).move_to(midtop=self.rect.midbottom)
        else:
            bottom_rect = pygame.Rect(self.rect.left, self.rect.bottom, self.rect.width, 2)
        self.on_floor = True if bottom_rect.collidelist([sprite.rect for sprite in self.collisions_sprites]) != -1 else False

    def collision(self, direction):
        for sprite in self.collisions_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == 'horizontal':
                    if self.direction.x > 0:
                        self.rect.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.rect.left = sprite.rect.right
                if direction == 'vertical':
                    if self.direction.y > 0:
                        self.rect.bottom = sprite.rect.top
                        self.direction.y = 0
                    if self.direction.y < 0:
                        self.rect.top = sprite.rect.bottom
                        self.direction.y = 0


class PlatformEnemy(PlatformAnimation):
    def __init__(self, pos, frames, groups):
        super().__init__(pos, frames, groups)
        self.death_timer = PlatformTimer(200, func=self.kill)

    def destroy(self):
        self.death_timer.activate()
        self.animation_speed = 0
        self.image = pygame.mask.from_surface(self.image).to_surface()
        self.image.set_colorkey("black")

    def update(self, dt):
        self.death_timer.update()
        if not self.death_timer:
            self.animate(dt)
            self.move(dt)


class PlatformBees(PlatformEnemy):
    def __init__(self, pos, groups, frames, speed):
        super().__init__(pos, frames, groups)
        self.speed = speed
        self.amplitude = random.randint(500, 600)
        self.frequency = random.randint(400, 600)

    def bee_kill(self):
        if self.rect.right < -600:
            self.kill()

    def move(self, dt):
        self.rect.x -= self.speed * dt
        self.rect.y += math.sin(pygame.time.get_ticks() / self.frequency) * self.amplitude * dt
        self.bee_kill()


class PlatformWorms(PlatformEnemy):
    def __init__(self, rect, groups, frames):
        super().__init__(rect.topleft, frames, groups)
        self.worm_rect = rect
        self.rect.bottomleft = self.worm_rect.bottomleft
        self.direction = 1
        self.speed = random.randint(160, 200)

    def move(self, dt):
        self.rect.x += self.direction * self.speed * dt

    def constraint(self):
        if not self.worm_rect.contains(self.rect):
            self.direction *= -1
            self.frames = [pygame.transform.flip(surf, True, False) for surf in self.frames]

    def update(self, dt):
        super().update(dt)
        if not self.death_timer:
            self.constraint()


class PlatformAllSprites(pygame.sprite.Group):
    def __init__(self, target_surface):
        super().__init__()
        self.offset = pygame.Vector2()
        self.display_surface = target_surface

    def draw(self, target_pos):
        self.offset.x = target_pos[0] - WINDOW_WIDTH / 2
        self.offset.y = target_pos[1] - WINDOW_HEIGHT / 2
        for sprite in self:
            self.display_surface.blit(sprite.image, sprite.rect.topleft - self.offset)


class PlatformDisplay:
    """
    Platform Game Display (Native 1280x720 resolution)
    - Full native game physics, TMX map world, enemies (bees, worms), shooting, audio
    - Runs inside its exact 1280x720 canvas, centered within the 1920x1080 overworld
    - Overworld is completely stopped while playing
    - ESC returns smoothly to the overworld without crashing
    """
    def __init__(self, game_name="Platform"):
        self.game_name = game_name
        self.orig_width = WINDOW_WIDTH   # 1280
        self.orig_height = WINDOW_HEIGHT # 720
        self.game_surface = pygame.Surface((self.orig_width, self.orig_height))

        self.assets_loaded = False
        self.audios = None

    def _init_assets(self):
        if self.assets_loaded:
            return

        self.audios = {
            "impact": pygame.mixer.Sound(os.path.join(PLATFORM_BASE, "audio", "impact.ogg")),
            "music": pygame.mixer.Sound(os.path.join(PLATFORM_BASE, "audio", "music.wav")),
            "shoot": pygame.mixer.Sound(os.path.join(PLATFORM_BASE, "audio", "shoot.wav")),
        }

        self.player_frames = import_folder(os.path.join(PLATFORM_BASE, "images", "player"))
        self.bullet_surface = import_image(os.path.join(PLATFORM_BASE, "images", "gun", "bullet.png"))
        self.fire_surface = import_image(os.path.join(PLATFORM_BASE, "images", "gun", "fire.png"))
        self.bees_frames = import_folder(os.path.join(PLATFORM_BASE, "images", "enemies", "bee"))
        self.worm_frames = import_folder(os.path.join(PLATFORM_BASE, "images", "enemies", "worm"))

        self.assets_loaded = True

    def create_bees(self):
        PlatformBees(
            pos=(self.world_width + 100, random.randint(0, self.world_height)),
            groups=(self.all_sprites, self.enemy_sprites),
            frames=self.bees_frames,
            speed=random.randint(300, 500)
        )

    def create_bullet(self, pos, direction):
        x = pos[0] + direction * 34 if direction == 1 else pos[0] + direction * 34 - self.bullet_surface.get_width()
        bullet_surf = pygame.transform.flip(self.bullet_surface, True, False) if direction == -1 else self.bullet_surface
        PlatformBullet(bullet_surf, (x, pos[1]), direction, (self.all_sprites, self.bullet_sprites))
        PlatformFire(self.fire_surface, pos, self.all_sprites, self.player)
        if self.audios and self.audios.get("shoot"):
            self.audios["shoot"].play()

    def setup(self):
        self.all_sprites = PlatformAllSprites(self.game_surface)
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        self.bee_timer = PlatformTimer(800, func=self.create_bees, repeat=True, autostart=True)

        map_path = os.path.join(PLATFORM_BASE, "data", "maps", "world.tmx")
        tmx_map = load_pygame(map_path)

        self.world_width = tmx_map.width * TILE_SIZE
        self.world_height = tmx_map.height * TILE_SIZE

        try:
            self.audios["music"].set_volume(0.3)
            self.audios["music"].play(loops=-1)
        except Exception:
            pass

        for x, y, image in tmx_map.get_layer_by_name("Main").tiles():
            PlatformSprite((x * TILE_SIZE, y * TILE_SIZE), image, (self.all_sprites, self.collision_sprites))
        for x, y, image in tmx_map.get_layer_by_name("Decoration").tiles():
            PlatformSprite((x * TILE_SIZE, y * TILE_SIZE), image, self.all_sprites)
        for obj in tmx_map.get_layer_by_name("Entities"):
            if obj.name == "Player":
                self.player = PlatformPlayer((obj.x, obj.y), self.all_sprites, self.collision_sprites, self.player_frames, self.create_bullet)
            if obj.name == "Worm":
                worm_rect = pygame.FRect(obj.x, obj.y, obj.width, obj.height) if hasattr(pygame, 'FRect') else pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                PlatformWorms(worm_rect, (self.all_sprites, self.enemy_sprites), self.worm_frames)

    def colllisions(self):
        for bullet_sprite in self.bullet_sprites:
            sprite_collisions = pygame.sprite.spritecollide(bullet_sprite, self.enemy_sprites, False, pygame.sprite.collide_mask)
            if sprite_collisions:
                bullet_sprite.kill()
                if self.audios and self.audios.get("impact"):
                    self.audios["impact"].play()
                for sprite in sprite_collisions:
                    sprite.destroy()
                    self.enemy_sprites.remove(sprite)

        if hasattr(self, 'player') and self.player.alive():
            # Enemy collisions
            if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
                if not self.player.death_timer:
                    if self.audios and self.audios.get("impact"):
                        self.audios["impact"].play()
                    self.player.destroy()

            # Fall to death: player falls at least 500 pixels below the bottom of the map
            if self.player.rect.top > self.world_height + 500:
                if self.audios and self.audios.get("impact"):
                    self.audios["impact"].play()
                self.player.kill()

    def run(self, screen):
        self._init_assets()
        clock = pygame.time.Clock()
        hud_font = pygame.font.Font(None, 36)

        pos_x = (WIDTH - self.orig_width) // 2
        pos_y = (HEIGHT - self.orig_height) // 2

        playing_session = True
        while playing_session:
            self.setup()
            game_active = True
            player_lost = False

            while game_active:
                dt = clock.tick(FRAMERATE) / 1000

                # 1. Event Handling
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        try:
                            self.audios["music"].stop()
                        except Exception:
                            pass
                        return

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            try:
                                self.audios["music"].stop()
                            except Exception:
                                pass
                            return

                # 2. Updates
                self.all_sprites.update(dt)
                self.colllisions()
                self.bee_timer.update()

                # Check if player died and finished death animation
                if not self.player.alive():
                    game_active = False
                    player_lost = True

                # 3. Render onto 1280x720 canvas
                self.game_surface.fill(BG_COLOR)
                target_pos = self.player.rect.center if self.player.alive() else (self.world_width / 2, self.world_height / 2)
                self.all_sprites.draw(target_pos)

                # 4. Center 1280x720 canvas on 1920x1080 screen
                screen.fill((0, 0, 0))
                screen.blit(self.game_surface, (pos_x, pos_y))

                frame_rect = pygame.Rect(pos_x - 4, pos_y - 4, self.orig_width + 8, self.orig_height + 8)
                pygame.draw.rect(screen, (255, 110, 80), frame_rect, width=3, border_radius=6)

                hint = hud_font.render(
                    "PLATFORM  |  A/D or Arrows: Move  |  W/Up: Jump  |  Space: Shoot  |  ESC: Exit",
                    True,
                    (180, 180, 200)
                )
                screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

                pygame.display.update()

            # If player lost, show game over banner
            if player_lost:
                try:
                    self.audios["music"].stop()
                except Exception:
                    pass

                restart = self._show_game_over(screen, hud_font, pos_x, pos_y)
                if not restart:
                    return

    def _show_game_over(self, screen, hud_font, pos_x, pos_y):
        """Displays Game Over on the 1280x720 game screen."""
        self.game_surface.fill((30, 20, 25))
        font_big = pygame.font.Font(None, 96)
        font_sub = pygame.font.Font(None, 42)

        t1 = font_big.render("GAME OVER", True, (255, 80, 80))
        t2 = font_sub.render("Press ENTER to Respawn  |  ESC to Return to Overworld", True, (220, 220, 240))

        self.game_surface.blit(t1, t1.get_rect(center=(self.orig_width // 2, self.orig_height // 2 - 40)))
        self.game_surface.blit(t2, t2.get_rect(center=(self.orig_width // 2, self.orig_height // 2 + 50)))

        screen.fill((0, 0, 0))
        screen.blit(self.game_surface, (pos_x, pos_y))
        frame_rect = pygame.Rect(pos_x - 4, pos_y - 4, self.orig_width + 8, self.orig_height + 8)
        pygame.draw.rect(screen, (255, 110, 80), frame_rect, width=3, border_radius=6)

        hint = hud_font.render("ENTER: Restart  |  ESC: Return to Overworld", True, (180, 180, 200))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))
        pygame.display.update()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        return True
            pygame.time.Clock().tick(60)
        return False





