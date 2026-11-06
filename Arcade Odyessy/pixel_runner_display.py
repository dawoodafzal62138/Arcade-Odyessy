import os
import sys
import math
import random
from array import array
from pathlib import Path
import pygame
from settigns import WIDTH, HEIGHT, CURRENT_DIR

# =========================================================================
# PIXEL RUNNER (Native 800x400 resolution)
# Completely self-contained to avoid namespace collisions with Arcade Odyssey
#
# Enhanced Features:
# - Pixel-perfect mask collisions (pygame.sprite.collide_mask) for fair hitboxes
# - Infinite parallax scrolling ground and sky
# - Dynamic procedural clouds drifting across the upper sky
# - Jump & Double Jump with mid-air acrobatic spin/sparkles
# - Duck / Slide mechanic (S or Down Arrow) to glide under high-flying obstacles
# - Floating Collectible Gold Coins (+50 pts & sparkle bursts)
# - Run dust, jump impact puffs, slide friction sparks, and defeat particle explosions
# - Dynamic speed acceleration and diverse obstacle wave patterns
# - Authentic Pixeltype.ttf retro typography & audio sound effects
# - Persistent high score saved to /Pixel-Runner-game-main/highscore.txt
# - Seamless ESC transition returning to Overworld
# =========================================================================

RUNNER_BASE = str((CURRENT_DIR.parent / "Pixel-Runner-game-main").resolve())
HIGHSCORE_PATH = os.path.join(RUNNER_BASE, "highscore.txt")

GAME_WIDTH, GAME_HEIGHT = 800, 400
GROUND_Y = 300


def r_join(*args):
    return os.path.join(RUNNER_BASE, *args)


def make_synth_sound(pitch, seconds, volume=0.35, wave_type="sine"):
    """Generates clean retro arcade synthesized sound effect without external files."""
    rate = 44100
    count = int(rate * seconds)
    samples = array("h")
    for i in range(count):
        t = i / rate
        if wave_type == "square":
            val = 1.0 if math.sin(2 * math.pi * pitch * t) >= 0 else -1.0
        else:
            val = math.sin(2 * math.pi * pitch * t)
        fade = 1.0 - (i / count)
        samples.append(int(32000 * volume * val * fade))
    try:
        return pygame.mixer.Sound(buffer=samples.tobytes())
    except Exception:
        return None


# -------------------------------------------------------------------------
# PARTICLES
# -------------------------------------------------------------------------
class PixelParticle:
    def __init__(self, x, y, color, vx, vy, lifetime=0.4, size=3):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.lifetime -= dt

    def draw(self, surface):
        if self.lifetime > 0:
            alpha_ratio = max(0.0, self.lifetime / self.max_lifetime)
            current_size = max(1, int(self.size * alpha_ratio))
            pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), current_size, current_size))


# -------------------------------------------------------------------------
# COLLECTIBLE COIN
# -------------------------------------------------------------------------
class PixelCoin(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.base_size = 20
        self.image = pygame.Surface((self.base_size, self.base_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.animation_timer = random.uniform(0, math.pi * 2)
        self._render_coin(0)
        self.mask = pygame.mask.from_surface(self.image)

    def _render_coin(self, angle):
        """Draws a shimmering 3D rotating retro gold coin."""
        self.image.fill((0, 0, 0, 0))
        width_scale = max(0.15, abs(math.cos(angle)))
        w = int(self.base_size * width_scale)
        h = self.base_size
        x = (self.base_size - w) // 2
        y = 0

        # Coin outer gold ring
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.ellipse(self.image, (218, 165, 32), rect)
        # Inner shiny gold
        inner_rect = rect.inflate(-3 if w > 6 else -1, -3)
        if inner_rect.width > 2 and inner_rect.height > 2:
            pygame.draw.ellipse(self.image, (255, 215, 0), inner_rect)
            # Center star/spec highlight
            highlight_x = inner_rect.centerx
            highlight_y = inner_rect.centery
            pygame.draw.circle(self.image, (255, 255, 220), (highlight_x, highlight_y), max(1, w // 4))

    def update(self, dt, speed):
        self.animation_timer += dt * 6
        self._render_coin(self.animation_timer)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x -= int(speed * dt * 60)
        if self.rect.right < -50:
            self.kill()


# -------------------------------------------------------------------------
# PROCEDURAL CLOUDS
# -------------------------------------------------------------------------
class ProceduralCloud:
    def __init__(self, x, y, speed, scale=1.0):
        self.x = x
        self.y = y
        self.speed = speed
        self.scale = scale
        self.surf = self._create_cloud_surface()

    def _create_cloud_surface(self):
        w = int(90 * self.scale)
        h = int(32 * self.scale)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        col = (255, 255, 255, 190)
        c_mid = (240, 245, 255, 210)
        # Multi-circle cloud puff
        pygame.draw.circle(surf, col, (int(24 * self.scale), int(20 * self.scale)), int(12 * self.scale))
        pygame.draw.circle(surf, c_mid, (int(45 * self.scale), int(15 * self.scale)), int(16 * self.scale))
        pygame.draw.circle(surf, col, (int(66 * self.scale), int(20 * self.scale)), int(12 * self.scale))
        pygame.draw.rect(surf, col, (int(14 * self.scale), int(18 * self.scale), int(62 * self.scale), int(14 * self.scale)), border_radius=6)
        return surf

    def update(self, dt):
        self.x -= self.speed * dt * 60
        if self.x < -120:
            self.x = GAME_WIDTH + random.randint(20, 150)
            self.y = random.randint(20, 110)

    def draw(self, surface):
        surface.blit(self.surf, (int(self.x), int(self.y)))


# -------------------------------------------------------------------------
# PLAYER
# -------------------------------------------------------------------------
class RunnerPlayer(pygame.sprite.Sprite):
    def __init__(self, walk_frames, jump_surf, stand_surf, jump_sound):
        super().__init__()
        self.walk_frames = walk_frames
        self.jump_surf = jump_surf
        self.stand_surf = stand_surf
        self.jump_sound = jump_sound

        # Precompute slide surface (crouched profile: 70 wide x 38 tall)
        base_w, base_h = self.walk_frames[0].get_size()
        self.slide_surf = pygame.transform.scale(self.walk_frames[0], (int(base_w * 1.1), int(base_h * 0.45)))

        self.image = self.walk_frames[0]
        self.rect = self.image.get_rect(midbottom=(80, GROUND_Y))
        self.mask = pygame.mask.from_surface(self.image)

        self.gravity = 0
        self.walk_index = 0
        self.jump_count = 0  # 0: on ground, 1: first jump, 2: double jump
        self.is_sliding = False
        self.is_dead = False

    def handle_input(self, double_jump_sound):
        keys = pygame.key.get_pressed()

        # Duck / Slide while on ground
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and self.rect.bottom >= GROUND_Y:
            self.is_sliding = True
        else:
            self.is_sliding = False

    def jump(self, double_jump_sound=None):
        if self.rect.bottom >= GROUND_Y:
            # First jump from ground
            self.gravity = -17
            self.jump_count = 1
            if self.jump_sound:
                self.jump_sound.play()
            return "jump"
        elif self.jump_count == 1:
            # Double jump in mid-air!
            self.gravity = -14
            self.jump_count = 2
            if double_jump_sound:
                double_jump_sound.play()
            return "double_jump"
        return None

    def apply_physics(self, dt):
        self.gravity += 50 * dt  # Realistic snappy gravity
        self.rect.y += int(self.gravity)

        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.gravity = 0
            self.jump_count = 0

    def animate(self, dt):
        if self.rect.bottom < GROUND_Y:
            # In air: use jump pose
            self.image = self.jump_surf
        elif self.is_sliding:
            # Sliding crouched pose
            self.image = self.slide_surf
        else:
            # Normal walk animation
            self.walk_index += 10 * dt
            if self.walk_index >= len(self.walk_frames):
                self.walk_index = 0
            self.image = self.walk_frames[int(self.walk_index)]

        # Maintain exact ground alignment
        prev_midbottom = self.rect.midbottom
        self.rect = self.image.get_rect(midbottom=prev_midbottom)

        # Precise pixel-perfect collision mask updated every frame!
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt, double_jump_sound=None):
        self.handle_input(double_jump_sound)
        self.apply_physics(dt)
        self.animate(dt)


# -------------------------------------------------------------------------
# OBSTACLE (Snail & Fly)
# -------------------------------------------------------------------------
class RunnerObstacle(pygame.sprite.Sprite):
    def __init__(self, obs_type, frames, spawn_x=None, y_override=None, groups=()):
        super().__init__(groups)
        self.obs_type = obs_type
        self.frames = frames
        self.anim_index = 0
        self.image = self.frames[0]

        if spawn_x is None:
            spawn_x = random.randint(860, 1020)

        if y_override is not None:
            y_pos = y_override
        elif obs_type == "fly":
            # Fly height: default 230 allows sliding underneath!
            y_pos = random.choice([230, 230, 280])
        else:
            # Snail on the ground
            y_pos = GROUND_Y

        self.rect = self.image.get_rect(midbottom=(spawn_x, y_pos))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt, speed):
        self.anim_index += 8 * dt
        if self.anim_index >= len(self.frames):
            self.anim_index = 0
        self.image = self.frames[int(self.anim_index)]
        self.mask = pygame.mask.from_surface(self.image)

        self.rect.x -= int(speed * dt * 60)
        if self.rect.right < -80:
            self.kill()


# -------------------------------------------------------------------------
# MAIN PIXEL RUNNER DISPLAY CLASS
# -------------------------------------------------------------------------
class PixelRunnerDisplay:
    """
    Pixel Runner Game Display (Native 800x400 resolution)
    - Full authentic pixel art runner with parallax infinite scrolling
    - Precise mask collisions (pygame.sprite.collide_mask)
    - Double Jump & Crouch/Slide under obstacles
    - Collectible shimmering gold coins with sparkle FX
    - Procedural clouds & dynamic particle bursts (dust, sparkles, defeat)
    - Persistent High Score saved to /Pixel-Runner-game-main/highscore.txt
    - Rendered centered on 1920x1080 Overworld with neon arcade frame
    - Overworld is 100% frozen while in minigame
    - ESC exits cleanly to Overworld
    """
    def __init__(self, game_name="Pixel-Runner-game-main"):
        self.game_name = game_name
        self.orig_width = GAME_WIDTH   # 800
        self.orig_height = GAME_HEIGHT # 400
        self.game_surface = pygame.Surface((self.orig_width, self.orig_height))

        self.assets_loaded = False
        self.high_score = self.load_high_score()

    def load_high_score(self):
        if os.path.exists(HIGHSCORE_PATH):
            try:
                with open(HIGHSCORE_PATH, "r") as f:
                    return int(f.read().strip())
            except Exception:
                return 0
        return 0

    def save_high_score(self, score):
        try:
            with open(HIGHSCORE_PATH, "w") as f:
                f.write(str(score))
        except Exception:
            pass

    def _init_assets(self):
        if self.assets_loaded:
            return

        gfx = r_join("resources", "graphics")
        audio = r_join("resources", "audio")
        font_dir = r_join("resources", "font")

        # Backgrounds
        self.sky_surf = pygame.image.load(os.path.join(gfx, "Sky.png")).convert()
        self.ground_surf = pygame.image.load(os.path.join(gfx, "ground.png")).convert()

        # Player frames
        p1 = pygame.image.load(os.path.join(gfx, "Player", "player_walk_1.png")).convert_alpha()
        p2 = pygame.image.load(os.path.join(gfx, "Player", "player_walk_2.png")).convert_alpha()
        self.player_walk_frames = [p1, p2]
        self.player_jump_surf = pygame.image.load(os.path.join(gfx, "Player", "jump.png")).convert_alpha()
        self.player_stand_surf = pygame.image.load(os.path.join(gfx, "Player", "player_stand.png")).convert_alpha()

        # Obstacle frames
        f1 = pygame.image.load(os.path.join(gfx, "Fly", "Fly1.png")).convert_alpha()
        f2 = pygame.image.load(os.path.join(gfx, "Fly", "Fly2.png")).convert_alpha()
        self.fly_frames = [f1, f2]

        s1 = pygame.image.load(os.path.join(gfx, "snail", "snail1.png")).convert_alpha()
        s2 = pygame.image.load(os.path.join(gfx, "snail", "snail2.png")).convert_alpha()
        self.snail_frames = [s1, s2]

        # Audio
        jump_path = os.path.join(audio, "jump.mp3")
        try:
            self.jump_sound = pygame.mixer.Sound(jump_path)
            self.jump_sound.set_volume(0.4)
        except Exception:
            self.jump_sound = make_synth_sound(450, 0.12, 0.4)

        music_path = os.path.join(audio, "music.wav")
        try:
            self.bg_music = pygame.mixer.Sound(music_path)
            self.bg_music.set_volume(0.18)
        except Exception:
            self.bg_music = None

        # Synthesized sound effects
        self.double_jump_sound = make_synth_sound(720, 0.14, volume=0.35)
        self.coin_sound = make_synth_sound(1040, 0.09, volume=0.35)
        self.game_over_sound = make_synth_sound(140, 0.35, volume=0.5, wave_type="square")
        self.speedup_sound = make_synth_sound(880, 0.18, volume=0.3)

        # Fonts
        font_path = os.path.join(font_dir, "Pixeltype.ttf")
        try:
            if os.path.exists(font_path):
                self.font_title = pygame.font.Font(font_path, 68)
                self.font_score = pygame.font.Font(font_path, 46)
                self.font_sub = pygame.font.Font(font_path, 34)
                self.font_hud = pygame.font.Font(font_path, 28)
            else:
                raise Exception("Font file missing")
        except Exception:
            self.font_title = pygame.font.Font(None, 68)
            self.font_score = pygame.font.Font(None, 46)
            self.font_sub = pygame.font.Font(None, 34)
            self.font_hud = pygame.font.Font(None, 28)

        self.assets_loaded = True

    def run(self, screen):
        self._init_assets()
        clock = pygame.time.Clock()
        outer_hud_font = pygame.font.Font(None, 34)

        pos_x = (WIDTH - self.orig_width) // 2
        pos_y = (HEIGHT - self.orig_height) // 2

        if self.bg_music:
            try:
                self.bg_music.play(loops=-1)
            except Exception:
                pass

        session_running = True
        game_state = "MENU"  # "MENU", "PLAYING", "GAMEOVER"

        # Game run state variables
        player = None
        obstacle_group = pygame.sprite.Group()
        coin_group = pygame.sprite.Group()
        particles = []
        clouds = [
            ProceduralCloud(80, 40, speed=0.4, scale=1.1),
            ProceduralCloud(340, 80, speed=0.6, scale=0.85),
            ProceduralCloud(620, 30, speed=0.35, scale=1.3),
        ]

        ground_x = 0
        sky_x = 0
        game_speed = 6.0
        distance_meters = 0
        coins_collected = 0
        total_score = 0
        screenshake = 0.0
        flash_text = ""
        flash_timer = 0

        # Spawning timers
        obstacle_spawn_timer = 0
        obstacle_interval = 1.4  # seconds
        coin_spawn_timer = 0
        coin_interval = 2.2      # seconds

        while session_running:
            dt = clock.tick(60) / 1000.0

            # -------------------------------------------------------------
            # 1. EVENT HANDLING
            # -------------------------------------------------------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if self.bg_music:
                        try:
                            self.bg_music.stop()
                        except Exception:
                            pass
                    return

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.bg_music:
                            try:
                                self.bg_music.stop()
                            except Exception:
                                pass
                        return

                    if game_state == "MENU":
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_w, pygame.K_UP):
                            # Start fresh run
                            game_state = "PLAYING"
                            player = RunnerPlayer(
                                self.player_walk_frames,
                                self.player_jump_surf,
                                self.player_stand_surf,
                                self.jump_sound
                            )
                            obstacle_group.empty()
                            coin_group.empty()
                            particles.clear()
                            game_speed = 6.0
                            distance_meters = 0
                            coins_collected = 0
                            total_score = 0
                            obstacle_spawn_timer = 0
                            coin_spawn_timer = 0
                            screenshake = 0.0
                            flash_text = ""

                    elif game_state == "PLAYING":
                        if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                            jump_type = player.jump(self.double_jump_sound)
                            if jump_type == "jump":
                                # Ground jump dust puff
                                for _ in range(6):
                                    particles.append(PixelParticle(
                                        player.rect.centerx + random.randint(-15, 15),
                                        GROUND_Y - 2,
                                        (210, 200, 190),
                                        random.uniform(-2, 2),
                                        random.uniform(-1.5, -0.2),
                                        lifetime=0.3,
                                        size=4
                                    ))
                            elif jump_type == "double_jump":
                                # Mid-air double jump sparkles!
                                for _ in range(10):
                                    particles.append(PixelParticle(
                                        player.rect.centerx + random.randint(-12, 12),
                                        player.rect.centery + random.randint(-10, 10),
                                        (255, 235, 100),
                                        random.uniform(-3, 3),
                                        random.uniform(-3, 1),
                                        lifetime=0.45,
                                        size=4
                                    ))

                    elif game_state == "GAMEOVER":
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_w, pygame.K_UP):
                            game_state = "PLAYING"
                            player = RunnerPlayer(
                                self.player_walk_frames,
                                self.player_jump_surf,
                                self.player_stand_surf,
                                self.jump_sound
                            )
                            obstacle_group.empty()
                            coin_group.empty()
                            particles.clear()
                            game_speed = 6.0
                            distance_meters = 0
                            coins_collected = 0
                            total_score = 0
                            obstacle_spawn_timer = 0
                            coin_spawn_timer = 0
                            screenshake = 0.0
                            flash_text = ""

            # -------------------------------------------------------------
            # 2. UPDATES & GAMEPLAY LOGIC
            # -------------------------------------------------------------
            if game_state == "PLAYING":
                # Increase game speed gradually
                game_speed += 0.05 * dt
                if game_speed > 13.5:
                    game_speed = 13.5

                distance_meters += int(game_speed * dt * 2.5)
                total_score = distance_meters + (coins_collected * 50)

                if total_score > self.high_score:
                    self.high_score = total_score
                    self.save_high_score(self.high_score)

                # Milestone notifications
                if distance_meters > 0 and distance_meters % 500 < 5:
                    flash_text = f"MILESTONE: {distance_meters}m!"
                    flash_timer = 1.5

                if flash_timer > 0:
                    flash_timer -= dt

                # Parallax Scrolling
                ground_x -= game_speed * dt * 60
                if ground_x <= -800:
                    ground_x += 800

                sky_x -= (game_speed * 0.15) * dt * 60
                if sky_x <= -800:
                    sky_x += 800

                # Clouds
                for cloud in clouds:
                    cloud.update(dt)

                # Player update
                player.update(dt, self.double_jump_sound)

                # Running dust particles
                if player.rect.bottom >= GROUND_Y and not player.is_sliding:
                    if random.random() < 0.35:
                        particles.append(PixelParticle(
                            player.rect.left + 5,
                            GROUND_Y - 2,
                            (200, 190, 180),
                            random.uniform(-2.5, -0.8),
                            random.uniform(-0.8, -0.1),
                            lifetime=0.25,
                            size=3
                        ))
                elif player.is_sliding:
                    # Slide sparks
                    for _ in range(2):
                        particles.append(PixelParticle(
                            player.rect.centerx + random.randint(-15, 15),
                            GROUND_Y - 2,
                            random.choice([(255, 180, 50), (255, 230, 100), (200, 190, 180)]),
                            random.uniform(-3.5, -1.0),
                            random.uniform(-1.5, -0.2),
                            lifetime=0.3,
                            size=3
                        ))

                # ---------------------------------------------------------
                # OBSTACLE SPAWNING
                # ---------------------------------------------------------
                obstacle_spawn_timer += dt
                if obstacle_spawn_timer >= obstacle_interval:
                    obstacle_spawn_timer = 0
                    obstacle_interval = max(0.9, random.uniform(1.2, 1.9) - (game_speed - 6) * 0.06)

                    # Choose obstacle pattern
                    choice = random.random()
                    if choice < 0.45:
                        # Single Snail
                        RunnerObstacle("snail", self.snail_frames, groups=obstacle_group)
                    elif choice < 0.75:
                        # Fly at high or mid height
                        fly_y = 230 if random.random() < 0.75 else 280
                        RunnerObstacle("fly", self.fly_frames, y_override=fly_y, groups=obstacle_group)
                    elif choice < 0.90:
                        # Double Snail combo
                        RunnerObstacle("snail", self.snail_frames, spawn_x=880, groups=obstacle_group)
                        RunnerObstacle("snail", self.snail_frames, spawn_x=960, groups=obstacle_group)
                    else:
                        # Fly + Snail staggered combo!
                        RunnerObstacle("snail", self.snail_frames, spawn_x=880, groups=obstacle_group)
                        RunnerObstacle("fly", self.fly_frames, spawn_x=1020, y_override=230, groups=obstacle_group)

                # ---------------------------------------------------------
                # COIN SPAWNING
                # ---------------------------------------------------------
                coin_spawn_timer += dt
                if coin_spawn_timer >= coin_interval:
                    coin_spawn_timer = 0
                    coin_interval = random.uniform(1.8, 3.2)
                    coin_y = random.choice([275, 210, 160])
                    # Spawn row of 1 to 3 coins
                    coin_count = random.choice([1, 2, 3])
                    for i in range(coin_count):
                        PixelCoin((900 + i * 40, coin_y), coin_group)

                # Update entities
                obstacle_group.update(dt, game_speed)
                coin_group.update(dt, game_speed)

                # ---------------------------------------------------------
                # COIN COLLECTION
                # ---------------------------------------------------------
                collected_coins = pygame.sprite.spritecollide(player, coin_group, True, pygame.sprite.collide_mask)
                for c in collected_coins:
                    coins_collected += 1
                    if self.coin_sound:
                        self.coin_sound.play()
                    # Gold sparkle burst
                    for _ in range(8):
                        particles.append(PixelParticle(
                            c.rect.centerx,
                            c.rect.centery,
                            random.choice([(255, 215, 0), (255, 255, 180), (255, 180, 0)]),
                            random.uniform(-2.5, 2.5),
                            random.uniform(-2.5, 2.5),
                            lifetime=0.35,
                            size=4
                        ))

                # ---------------------------------------------------------
                # PRECISE MASK COLLISION (PLAYER VS OBSTACLES)
                # ---------------------------------------------------------
                collided = pygame.sprite.spritecollide(player, obstacle_group, False, pygame.sprite.collide_mask)
                if collided:
                    game_state = "GAMEOVER"
                    screenshake = 14.0
                    if self.game_over_sound:
                        self.game_over_sound.play()
                    # Defeat particle burst
                    for _ in range(25):
                        particles.append(PixelParticle(
                            player.rect.centerx,
                            player.rect.centery,
                            random.choice([(255, 70, 70), (255, 200, 50), (255, 255, 255)]),
                            random.uniform(-4, 4),
                            random.uniform(-4, 2),
                            lifetime=0.6,
                            size=random.randint(3, 5)
                        ))

            # Update particles
            for p in particles[:]:
                p.update(dt)
                if p.lifetime <= 0:
                    particles.remove(p)

            if screenshake > 0:
                screenshake = max(0.0, screenshake - 35.0 * dt)

            # -------------------------------------------------------------
            # 3. DRAW TO 800x400 GAME CANVAS
            # -------------------------------------------------------------
            # Sky (Parallax)
            self.game_surface.blit(self.sky_surf, (sky_x, 0))
            self.game_surface.blit(self.sky_surf, (sky_x + 800, 0))

            # Clouds
            for cloud in clouds:
                cloud.draw(self.game_surface)

            # Ground (Parallax)
            self.game_surface.blit(self.ground_surf, (ground_x, GROUND_Y))
            self.game_surface.blit(self.ground_surf, (ground_x + 800, GROUND_Y))

            # Particles behind player/coins
            for p in particles:
                p.draw(self.game_surface)

            # Draw Coins & Obstacles
            coin_group.draw(self.game_surface)
            obstacle_group.draw(self.game_surface)

            # Draw Player
            if game_state == "PLAYING" and player:
                self.game_surface.blit(player.image, player.rect)

            # -------------------------------------------------------------
            # HUD / UI OVERLAYS
            # -------------------------------------------------------------
            if game_state == "PLAYING":
                # Score HUD (Left)
                sc_txt = self.font_score.render(f"SCORE: {total_score}", False, (30, 30, 30))
                self.game_surface.blit(sc_txt, (25, 18))
                sc_txt_glow = self.font_score.render(f"SCORE: {total_score}", False, (255, 255, 255))
                self.game_surface.blit(sc_txt_glow, (23, 16))

                # Coins HUD (Center-Left)
                cn_txt = self.font_sub.render(f"COINS: {coins_collected}", False, (218, 165, 32))
                self.game_surface.blit(cn_txt, (260, 20))

                # Best Score HUD (Right)
                hs_txt = self.font_sub.render(f"BEST: {self.high_score}", False, (60, 60, 80))
                self.game_surface.blit(hs_txt, (GAME_WIDTH - hs_txt.get_width() - 25, 20))

                # Milestone flash banner
                if flash_timer > 0 and flash_text:
                    m_surf = self.font_sub.render(flash_text, False, (255, 230, 60))
                    m_rect = m_surf.get_rect(center=(GAME_WIDTH // 2, 70))
                    # Background pill with proper alpha (must use separate SRCALPHA surface)
                    pill = pygame.Surface((m_rect.width + 24, m_rect.height + 8), pygame.SRCALPHA)
                    pill.fill((20, 20, 30, 200))
                    self.game_surface.blit(pill, (m_rect.x - 12, m_rect.y - 4))
                    self.game_surface.blit(m_surf, m_rect)

            elif game_state == "MENU":
                # Tint overlay
                overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
                overlay.fill((10, 25, 40, 160))
                self.game_surface.blit(overlay, (0, 0))

                # Title
                t_shadow = self.font_title.render("PIXEL RUNNER", False, (10, 20, 30))
                t_surf = self.font_title.render("PIXEL RUNNER", False, (111, 220, 180))
                self.game_surface.blit(t_shadow, t_shadow.get_rect(center=(GAME_WIDTH // 2 + 2, 72)))
                self.game_surface.blit(t_surf, t_surf.get_rect(center=(GAME_WIDTH // 2, 70)))

                # Standing Player Preview (scaled x2)
                preview_surf = pygame.transform.rotozoom(self.player_stand_surf, 0, 1.8)
                self.game_surface.blit(preview_surf, preview_surf.get_rect(center=(GAME_WIDTH // 2, 185)))

                # Subtext & Prompts
                p_surf = self.font_score.render("Press SPACE or ENTER to Start", False, (255, 255, 255))
                self.game_surface.blit(p_surf, p_surf.get_rect(center=(GAME_WIDTH // 2, 280)))

                hint_surf = self.font_hud.render(
                    "SPACE / W: Jump & Double Jump  |  S / DOWN: Duck & Slide  |  Collect Coins!",
                    False,
                    (200, 225, 240)
                )
                self.game_surface.blit(hint_surf, hint_surf.get_rect(center=(GAME_WIDTH // 2, 330)))

                if self.high_score > 0:
                    best_surf = self.font_sub.render(f"Current Record: {self.high_score}", False, (255, 215, 0))
                    self.game_surface.blit(best_surf, best_surf.get_rect(center=(GAME_WIDTH // 2, 365)))

            elif game_state == "GAMEOVER":
                # Dark tint overlay
                overlay = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
                overlay.fill((30, 10, 20, 190))
                self.game_surface.blit(overlay, (0, 0))

                # Game Over Header
                go_shadow = self.font_title.render("GAME OVER", False, (20, 0, 0))
                go_surf = self.font_title.render("GAME OVER", False, (255, 75, 90))
                self.game_surface.blit(go_shadow, go_shadow.get_rect(center=(GAME_WIDTH // 2 + 2, 72)))
                self.game_surface.blit(go_surf, go_surf.get_rect(center=(GAME_WIDTH // 2, 70)))

                # Score Breakdown Box (use SRCALPHA surface for real transparency)
                stats_box = pygame.Rect(GAME_WIDTH // 2 - 200, 120, 400, 150)
                stats_bg = pygame.Surface((400, 150), pygame.SRCALPHA)
                stats_bg.fill((20, 15, 25, 230))
                self.game_surface.blit(stats_bg, stats_box.topleft)
                pygame.draw.rect(self.game_surface, (255, 80, 100), stats_box, width=3, border_radius=12)

                s1 = self.font_sub.render(f"Distance Ran: {distance_meters}m", False, (220, 220, 240))
                s2 = self.font_sub.render(f"Coins Collected: {coins_collected} (+{coins_collected * 50} pts)", False, (255, 215, 0))
                s3 = self.font_score.render(f"FINAL SCORE: {total_score}", False, (255, 255, 255))

                self.game_surface.blit(s1, s1.get_rect(center=(GAME_WIDTH // 2, 155)))
                self.game_surface.blit(s2, s2.get_rect(center=(GAME_WIDTH // 2, 195)))
                self.game_surface.blit(s3, s3.get_rect(center=(GAME_WIDTH // 2, 235)))

                # High Score banner
                if total_score >= self.high_score and total_score > 0:
                    hs_badge = self.font_sub.render("★ NEW BEST RECORD! ★", False, (255, 230, 60))
                else:
                    hs_badge = self.font_hud.render(f"Best Score: {self.high_score}", False, (180, 180, 200))
                self.game_surface.blit(hs_badge, hs_badge.get_rect(center=(GAME_WIDTH // 2, 295)))

                # Retry Prompt
                retry_surf = self.font_sub.render("Press SPACE to Play Again  |  ESC to Return to Overworld", False, (255, 255, 255))
                self.game_surface.blit(retry_surf, retry_surf.get_rect(center=(GAME_WIDTH // 2, 350)))

            # -------------------------------------------------------------
            # 4. BLIT CENTERED ON 1920x1080 SCREEN WITH NEON BORDER
            # -------------------------------------------------------------
            screen.fill((0, 0, 0))

            int_shake = int(screenshake)
            shake_x = random.randint(-int_shake, int_shake) if int_shake > 0 else 0
            shake_y = random.randint(-int_shake, int_shake) if int_shake > 0 else 0

            screen.blit(self.game_surface, (pos_x + shake_x, pos_y + shake_y))

            frame_rect = pygame.Rect(pos_x - 4, pos_y - 4, self.orig_width + 8, self.orig_height + 8)
            pygame.draw.rect(screen, (0, 255, 180), frame_rect, width=3, border_radius=6)

            outer_hint = outer_hud_font.render(
                "PIXEL RUNNER  |  Space/W/Up: Jump & Double Jump  |  S/Down: Duck & Slide  |  ESC: Exit",
                True,
                (180, 200, 210)
            )
            screen.blit(outer_hint, outer_hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

            pygame.display.update()
