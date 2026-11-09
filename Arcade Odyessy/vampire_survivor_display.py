from arcade_screen import draw_arcade, arcade_mouse
import os
import sys
import math
import random
from math import atan2, degrees
from os import walk
from pathlib import Path
import pygame
from pytmx.util_pygame import load_pygame
from settigns import WIDTH, HEIGHT, CURRENT_DIR

# =========================================================================
# VAMPIRE SURVIVOR (Native 1280x720 resolution)
# Completely self-contained to avoid namespace collisions with Arcade Odyssey
# =========================================================================
VAMPIRE_BASE = str((CURRENT_DIR.parent / "Vampire survivor").resolve())

GAME_WIDTH, GAME_HEIGHT = 1280, 720
TILE_SIZE = 64


def v_join(*args):
    return os.path.join(VAMPIRE_BASE, *args)


class VampireSprite(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)
        self.ground = True


class VampireCollisionSprite(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)


class VampireGun(pygame.sprite.Sprite):
    def __init__(self, player, groups, gun_surf):
        self.player = player
        self.distance = 140
        self.player_direction = pygame.math.Vector2(0, 1)

        super().__init__(groups)
        self.surf = gun_surf
        self.image = self.surf
        self.rect = self.image.get_frect(center=self.player.rect.center + self.player_direction * self.distance)

    def rotation(self):
        angle = degrees(atan2(self.player_direction.x, self.player_direction.y)) - 90
        if self.player_direction.x > 0:
            self.image = pygame.transform.rotozoom(self.surf, angle, 1)
        else:
            self.image = pygame.transform.rotozoom(self.surf, abs(angle), 1)
            self.image = pygame.transform.flip(self.image, False, True)

    def get_direction(self, local_mouse):
        player_screen_pos = pygame.math.Vector2((GAME_WIDTH / 2, GAME_HEIGHT / 2))
        direction = local_mouse - player_screen_pos
        if direction.length() > 0:
            self.player_direction = direction.normalize()

    def update(self, dt, local_mouse=None):
        if local_mouse is not None:
            self.get_direction(local_mouse)
        self.rotation()
        self.rect.center = self.player.rect.center + self.player_direction * self.distance


class VampireBullet(pygame.sprite.Sprite):
    def __init__(self, surf, pos, direction, groups):
        super().__init__(*groups)
        self.image = surf
        self.rect = self.image.get_frect(center=pos)
        self.speed = 1200
        self.direction = direction
        self.time = pygame.time.get_ticks()
        self.life_time = 1000

    def update(self, dt):
        self.rect.center += self.speed * self.direction * dt
        if pygame.time.get_ticks() - self.time > self.life_time:
            self.kill()


class VampireEnemy(pygame.sprite.Sprite):
    def __init__(self, frames, pos, player, collision_sprites, groups):
        super().__init__(*groups)
        self.player = player
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.direction = pygame.math.Vector2()
        self.animation_speed = 6

        self.rect = self.image.get_frect(center=pos)
        self.hit_box = self.rect.inflate(-20, 40)

        self.speed = 300
        self.collision_sprites = collision_sprites
        self.death_time = 0
        self.death_duration = 400

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def move(self, dt):
        player_pos = pygame.math.Vector2(self.player.rect.center)
        enemy_pos = pygame.math.Vector2(self.rect.center)
        direction = player_pos - enemy_pos
        if direction.length() > 0:
            self.direction = direction.normalize()

        self.hit_box.x += self.direction.x * self.speed * dt
        self.collisions("horizontal")
        self.hit_box.y += self.direction.y * self.speed * dt
        self.collisions("vertical")
        self.rect.center = self.hit_box.center

    def collisions(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hit_box):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hit_box.right = sprite.rect.left
                    if self.direction.x < 0: self.hit_box.left = sprite.rect.right
                else:
                    if self.direction.y > 0: self.hit_box.bottom = sprite.rect.top
                    if self.direction.y < 0: self.hit_box.top = sprite.rect.bottom

    def destroy(self):
        surf = pygame.mask.from_surface(self.frames[0]).to_surface()
        surf.set_colorkey("black")
        self.image = surf
        self.death_time = pygame.time.get_ticks()

    def death_timer(self):
        if pygame.time.get_ticks() - self.death_time > self.death_duration:
            self.kill()

    def update(self, dt):
        if self.death_time == 0:
            self.move(dt)
            self.animate(dt)
        else:
            self.death_timer()


class VampireCursor(pygame.sprite.Sprite):
    def __init__(self, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect()

    def update(self, dt, local_mouse=None):
        if local_mouse is not None:
            self.rect.center = (local_mouse.x, local_mouse.y)


class VampirePlayer(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprite, frames):
        super().__init__(groups)
        self.frames = frames
        self.frames_index, self.state = 0, "down"
        self.image = self.frames["down"][0]
        self.rect = self.image.get_frect(center=pos)
        self.hit_box = self.rect.inflate(-55, -90)
        self.collision_sprite = collision_sprite

        self.health = 10
        self.max_health = 10

        self.direction = pygame.math.Vector2()
        self.speed = 450

        self.hit_time = -1000
        self.hit_duration = 300
        self.mask = pygame.mask.from_surface(self.image)

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w])
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

    def movement(self, dt):
        self.hit_box.x += self.direction.x * self.speed * dt
        self.collisions("horizontal")
        self.hit_box.y += self.direction.y * self.speed * dt
        self.collisions("vertical")
        self.rect.center = self.hit_box.center

    def collisions(self, direction):
        for sprite in self.collision_sprite:
            if sprite.rect.colliderect(self.hit_box):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hit_box.right = sprite.rect.left
                    if self.direction.x < 0: self.hit_box.left = sprite.rect.right
                else:
                    if self.direction.y > 0: self.hit_box.bottom = sprite.rect.top
                    if self.direction.y < 0: self.hit_box.top = sprite.rect.bottom

    def animation(self, dt):
        if self.direction.x != 0:
            self.state = "right" if self.direction.x > 0 else "left"
        if self.direction.y != 0:
            self.state = "down" if self.direction.y > 0 else "up"

        self.frames_index += 7 * dt
        if self.direction.magnitude() == 0:
            self.image = self.frames[self.state][0]
        else:
            self.image = self.frames[self.state][int(self.frames_index) % len(self.frames[self.state])]

    def hit(self):
        self.hit_time = pygame.time.get_ticks()

    def hit_timer(self):
        if pygame.time.get_ticks() - self.hit_time < self.hit_duration:
            mask = pygame.mask.from_surface(self.image)
            mask_surf = mask.to_surface()
            mask_surf.set_colorkey("black")
            self.image = mask_surf

    def update(self, dt):
        self.input()
        self.movement(dt)
        self.animation(dt)
        self.hit_timer()
        self.mask = pygame.mask.from_surface(self.image)


class VampireAllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.offset = pygame.math.Vector2(100, 100)

    def draw(self, target_pos, surface):
        ground_sprite = [sprite for sprite in self if hasattr(sprite, "ground")]
        object_sprite = [sprite for sprite in self if not hasattr(sprite, "ground")]
        self.offset.x = -(target_pos[0] - GAME_WIDTH / 2)
        self.offset.y = -(target_pos[1] - GAME_HEIGHT / 2)
        for layer in [ground_sprite, object_sprite]:
            for sprite in sorted(layer, key=lambda sprite: sprite.rect.centery):
                surface.blit(sprite.image, sprite.rect.topleft + self.offset)


class VampireSurvivorDisplay:
    """
    Vampire Survivor (Vampire Shooter) Game Display (Native 1280x720 resolution)
    - Full authentic top-down shooting, waves of enemies, gun rotation, hearts HUD
    - Runs inside its exact 1280x720 canvas, centered within the 1920x1080 overworld
    - Overworld is completely stopped while playing
    - ESC returns smoothly to the overworld without crashing
    """
    def __init__(self, game_name="Vampire survivor"):
        self.game_name = game_name
        self.orig_width = GAME_WIDTH   # 1280
        self.orig_height = GAME_HEIGHT # 720
        self.game_surface = pygame.Surface((self.orig_width, self.orig_height))

        self.assets_loaded = False
        self.audios = None

    def _init_assets(self):
        if self.assets_loaded:
            return

        # Audio
        self.shoot_sound = pygame.mixer.Sound(v_join("audio", "shoot.wav"))
        self.shoot_sound.set_volume(0.3)
        self.music = pygame.mixer.Sound(v_join("audio", "music.wav"))
        self.music.set_volume(0.2)
        self.impact_sound = pygame.mixer.Sound(v_join("audio", "impact.ogg"))
        self.impact_sound.set_volume(0.5)

        # Player frames
        self.player_frames = {"left": [], "right": [], "up": [], "down": []}
        for state in self.player_frames.keys():
            state_dir = v_join("images", "player", state)
            for folder_path, _, file_names in walk(state_dir):
                if file_names:
                    for f in sorted(file_names, key=lambda n: int(n.split(".")[0])):
                        surf = pygame.image.load(os.path.join(folder_path, f)).convert_alpha()
                        self.player_frames[state].append(surf)

        # Gun & Bullets
        self.gun_surface = pygame.image.load(v_join("images", "gun", "gun.png")).convert_alpha()
        self.bullet_surface = pygame.image.load(v_join("images", "gun", "bullet.png")).convert_alpha()

        # Enemy frames
        self.enemy_frames = {}
        enemy_root = v_join("images", "enemies")
        if os.path.exists(enemy_root):
            folders = list(walk(enemy_root))[0][1]
            for folder in folders:
                self.enemy_frames[folder] = []
                f_path = os.path.join(enemy_root, folder)
                for folder_path, _, file_names in walk(f_path):
                    for f in sorted(file_names, key=lambda n: int(n.split(".")[0])):
                        surf = pygame.image.load(os.path.join(folder_path, f)).convert_alpha()
                        self.enemy_frames[folder].append(surf)

        # Cursor
        raw_cursor = pygame.image.load(v_join("images", "crossshair.png")).convert_alpha()
        self.cursor_image = pygame.transform.scale(raw_cursor, (70, 70))

        # Hearts
        heart_sheet = pygame.image.load(v_join("images", "16x16 Heart Health Red Horizontal.png")).convert_alpha()
        heart_full_raw = pygame.transform.scale2x(heart_sheet.subsurface((0, 0, 16, 16)))
        self.heart_full = heart_full_raw.copy()
        w, h = self.heart_full.get_size()
        for x in range(w):
            for y in range(h):
                r, g, b, a = self.heart_full.get_at((x, y))
                if a > 0 and (r > 60 or g > 40):
                    r = min(255, int(r * 1.8) + 30)
                    g = min(255, int(g * 1.1))
                    b = min(255, int(b * 1.1))
                    self.heart_full.set_at((x, y), (r, g, b, a))
        self.heart_empty = pygame.transform.scale2x(heart_sheet.subsurface((32, 0, 16, 16)))

        # Screens
        self.start_image = pygame.transform.smoothscale(
            pygame.image.load(v_join("images", "start.jpeg")).convert(), (GAME_WIDTH, GAME_HEIGHT)
        )
        self.game_over_image = pygame.transform.smoothscale(
            pygame.image.load(v_join("images", "gameover.jpeg")).convert(), (GAME_WIDTH, GAME_HEIGHT)
        )

        self.assets_loaded = True

    def setup(self):
        self.all_sprites = VampireAllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprite = pygame.sprite.Group()
        self.enemy_sprite = pygame.sprite.Group()
        self.crosshair_sprite = pygame.sprite.Group()

        self.spawn_pos = []

        map_data = load_pygame(v_join("data", "maps", "world.tmx"))

        for x, y, image in map_data.get_layer_by_name("Ground").tiles():
            VampireSprite(image, (x * TILE_SIZE, y * TILE_SIZE), self.all_sprites)
        for obj in map_data.get_layer_by_name("Objects"):
            VampireCollisionSprite(obj.image, (obj.x, obj.y), (self.all_sprites, self.collision_sprites))
        for obj in map_data.get_layer_by_name("Collisions"):
            VampireCollisionSprite(pygame.Surface((int(obj.width), int(obj.height))), (obj.x, obj.y), self.collision_sprites)
        for obj in map_data.get_layer_by_name("Entities"):
            if obj.name == "Player":
                self.player = VampirePlayer((obj.x, obj.y), self.all_sprites, self.collision_sprites, self.player_frames)
                self.gun = VampireGun(self.player, self.all_sprites, self.gun_surface)
            else:
                self.spawn_pos.append((obj.x, obj.y))

        self.cursor = VampireCursor(self.cursor_image, self.crosshair_sprite)

    def spawn_enemies(self):
        if not self.spawn_pos or self.cycle_count >= self.max_cycles:
            return

        pos = self.spawn_pos[self.current_spawn_index]
        if self.enemy_frames:
            enemy_type = random.choice(list(self.enemy_frames.values()))
            VampireEnemy(enemy_type, pos, self.player, self.collision_sprites, (self.all_sprites, self.enemy_sprite))

        self.current_spawn_index += 1
        if self.current_spawn_index >= len(self.spawn_pos):
            self.current_spawn_index = 0
            self.cycle_count += 1

    def health(self, target_surf):
        start_x, start_y = 20, 20
        spacing = 38
        for i in range(self.player.max_health):
            x = start_x + i * spacing
            y = start_y
            if i < self.player.health:
                target_surf.blit(self.heart_full, (x, y))
            else:
                target_surf.blit(self.heart_empty, (x, y))

    def run(self, screen):
        self._init_assets()
        clock = pygame.time.Clock()
        hud_font = pygame.font.Font(None, 36)

        pos_x = (WIDTH - self.orig_width) // 2
        pos_y = (HEIGHT - self.orig_height) // 2

        self.setup()

        # Hide system cursor while in this game (we use the crosshair sprite)
        pygame.mouse.set_visible(False)

        try:
            self.music.play(loops=-1)
        except Exception:
            pass

        # Game state variables
        start_game = False
        game_over = False
        can_shoot = True
        shoot_time = 0
        shoot_cooldown = 100
        last_damage_time = -600
        damage_cooldown = 600

        screenshake = 0
        transition = 0
        dead = 0
        kills = 0  # Track enemies killed

        current_spawn_index = 0
        cycle_count = 0
        self.current_spawn_index = 0
        self.cycle_count = 0
        self.max_cycles = 10
        spawn_timer = 0

        running = True
        while running:
            dt = clock.tick(60) / 1000
            raw_mouse = pygame.mouse.get_pos()
            local_mouse = pygame.math.Vector2(arcade_mouse(screen, raw_mouse, self.game_surface.get_size()))

            # -------------------------------------------------------------
            # EVENT HANDLING
            # -------------------------------------------------------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    if not start_game:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            start_game = True
                            screenshake = 16
                            transition = -30
                            dead = 0
                    elif game_over:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            # Restart match
                            self.setup()
                            start_game = True
                            game_over = False
                            dead = 0
                            kills = 0
                            screenshake = 16
                            transition = -30
                            self.cycle_count = 0
                            self.current_spawn_index = 0

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not start_game:
                        start_game = True
                        screenshake = 16
                        transition = -30
                        dead = 0
                    elif game_over:
                        self.setup()
                        start_game = True
                        game_over = False
                        dead = 0
                        kills = 0
                        screenshake = 16
                        transition = -30
                        self.cycle_count = 0
                        self.current_spawn_index = 0

            # -------------------------------------------------------------
            # GAMEPLAY UPDATE & RENDER
            # -------------------------------------------------------------
            if not start_game:
                self.game_surface.blit(self.start_image, (0, 0))

            elif game_over:
                self.game_surface.blit(self.game_over_image, (0, 0))

            else:
                # Shooting logic
                if not can_shoot:
                    if pygame.time.get_ticks() - shoot_time > shoot_cooldown:
                        can_shoot = True

                if pygame.mouse.get_pressed()[0] and can_shoot and not dead:
                    bullet_pos = self.gun.rect.center + self.gun.player_direction * 50
                    VampireBullet(self.bullet_surface, bullet_pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprite))
                    if self.shoot_sound:
                        self.shoot_sound.play()
                    shoot_time = pygame.time.get_ticks()
                    can_shoot = False

                # Spawning enemies
                spawn_timer += dt
                if spawn_timer >= 0.5:
                    spawn_timer = 0
                    self.spawn_enemies()

                # Screenshake decay
                screenshake = max(0, screenshake - 1)

                if dead:
                    dead += 1
                    if dead >= 5:
                        transition = min(transition + 1, 30)
                    if dead > 35:
                        game_over = True
                elif transition < 0:
                    transition += 1

                # Update sprites
                if not dead:
                    self.all_sprites.update(dt)
                    self.gun.update(dt, local_mouse)
                    self.crosshair_sprite.update(dt, local_mouse)

                    # Bullet vs Enemy collisions
                    for b in self.bullet_sprite:
                        hit_enemies = pygame.sprite.spritecollide(b, self.enemy_sprite, False, pygame.sprite.collide_mask)
                        if hit_enemies:
                            if self.impact_sound:
                                self.impact_sound.play()
                            for e in hit_enemies:
                                e.destroy()
                                kills += 1
                            b.kill()

                    # Player vs Enemy collisions
                    now = pygame.time.get_ticks()
                    if now - last_damage_time > damage_cooldown:
                        collided = pygame.sprite.spritecollide(self.player, self.enemy_sprite, False, pygame.sprite.collide_mask)
                        living = [e for e in collided if e.death_time == 0]
                        if living:
                            if self.impact_sound:
                                self.impact_sound.play()
                            self.player.health = max(0, self.player.health - 1)
                            last_damage_time = now
                            self.player.hit()
                            for e in living:
                                e.destroy()
                            if self.player.health <= 0 and not dead:
                                dead = 1
                                screenshake = max(screenshake, 25)
                                transition = 0
                                self.player.kill()
                                self.gun.kill()
                else:
                    self.all_sprites.update(dt)
                    self.crosshair_sprite.update(dt, local_mouse)

                # Draw scene onto 1280x720 canvas
                self.game_surface.fill("black")
                target = self.player.rect.center if hasattr(self, 'player') and self.player.alive() else (GAME_WIDTH / 2, GAME_HEIGHT / 2)
                self.all_sprites.draw(target, self.game_surface)

                if not dead:
                    self.crosshair_sprite.draw(self.game_surface)
                    self.health(self.game_surface)
                    # Kills score HUD (top-right)
                    kills_surf = hud_font.render(f"KILLS: {kills}", True, (255, 90, 90))
                    self.game_surface.blit(kills_surf, kills_surf.get_rect(topright=(GAME_WIDTH - 20, 20)))

                # Circle transition effect
                if transition:
                    transition_surface = pygame.Surface(self.game_surface.get_size())
                    radius = max(0, int((30 - abs(transition)) * 28))
                    if radius > 0:
                        pygame.draw.circle(
                            transition_surface,
                            (255, 255, 255),
                            (self.orig_width // 2, self.orig_height // 2),
                            radius
                        )
                    transition_surface.set_colorkey((255, 255, 255))
                    self.game_surface.blit(transition_surface, (0, 0))

            # -------------------------------------------------------------
            # BLIT CENTERED ON 1920x1080 SCREEN
            # -------------------------------------------------------------
            screen.fill((0, 0, 0))

            shake_x = random.randint(-screenshake, screenshake) if screenshake else 0
            shake_y = random.randint(-screenshake, screenshake) if screenshake else 0

            draw_arcade(screen, self.game_surface, (shake_x, shake_y))


            hint = hud_font.render(
                "VAMPIRE SURVIVOR  |  WASD: Move  |  Mouse: Aim  |  Left Click: Shoot  |  ESC: Exit",
                True,
                (180, 180, 200)
            )
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

            pygame.display.update()

        try:
            self.music.stop()
        except Exception:
            pass
        # Restore system cursor when leaving this game
        pygame.mouse.set_visible(True)

