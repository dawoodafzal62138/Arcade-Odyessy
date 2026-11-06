import os
import sys
import math
import random
from array import array
from pathlib import Path
import pygame
from settigns import WIDTH, HEIGHT, CURRENT_DIR

# =========================================================================
# PONG GAME (Native 1280x720 resolution)
# =========================================================================
PONG_BASE = str((CURRENT_DIR.parent / "Pong").resolve())
HIGHSCORE_PATH = os.path.join(PONG_BASE, "highscore.txt")

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
PADDLE_SIZE = (30, 160)
BALL_SIZE = 26

COLORS = {
    'paddle1': '#ee322c',         # Red (Player 1 - Right)
    'paddle2': '#1d70d8',         # Blue (Player 2 / AI - Left)
    'ball': '#ffffff',            # Crisp white ball
    'bg': '#001a24',              # Deep arcade blue/teal
    'center_line': '#004050',     # Court dividing line
    'hud': '#ffffff',
    'hud_dim': '#80a0b0',
    'accent': '#00ffcc',
}


def make_beep(pitch, seconds, volume=0.4):
    """Generates clean retro arcade synthesized sound effect."""
    rate = 44100
    count = int(rate * seconds)
    samples = array("h")
    for i in range(count):
        wave = math.sin(2 * math.pi * pitch * i / rate)
        fade = 1 - i / count
        samples.append(int(32000 * volume * wave * fade))
    try:
        return pygame.mixer.Sound(buffer=samples.tobytes())
    except Exception:
        return None


class PongPaddle(pygame.sprite.Sprite):
    def __init__(self, pos, color, is_player1=True):
        super().__init__()
        self.image = pygame.Surface(PADDLE_SIZE, pygame.SRCALPHA)
        pygame.draw.rect(self.image, color, pygame.Rect(0, 0, *PADDLE_SIZE), border_radius=8)
        self.rect = self.image.get_rect(center=pos)
        self.direction = 0
        self.speed = 600
        self.is_player1 = is_player1
        self.last_ai_mode = True

    def input(self, ball=None):
        keys = pygame.key.get_pressed()
        if self.is_player1:
            # Player 1 controls (Right Paddle): Up/Down or K/M
            self.direction = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        else:
            # Player 2 controls (Left Paddle): W/S
            p2_input = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
            if p2_input != 0:
                self.direction = p2_input
                self.last_ai_mode = False
            elif self.last_ai_mode and ball is not None:
                # Smooth adaptive AI when single-player
                diff = ball.rect.centery - self.rect.centery
                if abs(diff) > 20:
                    self.direction = 1 if diff > 0 else -1
                else:
                    self.direction = 0

    def update(self, dt, ball=None):
        self.input(ball)
        self.rect.centery += int(self.direction * self.speed * dt)
        if self.rect.top < 10:
            self.rect.top = 10
        if self.rect.bottom > WINDOW_HEIGHT - 10:
            self.rect.bottom = WINDOW_HEIGHT - 10


class PongBall(pygame.sprite.Sprite):
    def __init__(self, paddles, sounds):
        super().__init__()
        self.paddles = paddles
        self.sounds = sounds
        self.image = pygame.Surface((BALL_SIZE, BALL_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(self.image, COLORS['ball'], (BALL_SIZE // 2, BALL_SIZE // 2), BALL_SIZE // 2)
        self.rect = self.image.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))

        self.base_speed = 520
        self.speed = self.base_speed
        self.direction = pygame.Vector2(random.choice((-1, 1)), random.uniform(-0.5, 0.5)).normalize()
        self.active = True
        self.respawn_timer = 0
        self.rally_count = 0

    def reset(self, serve_direction=1):
        self.rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self.speed = self.base_speed
        self.direction = pygame.Vector2(serve_direction, random.uniform(-0.4, 0.4)).normalize()
        self.active = False
        self.respawn_timer = 60  # Brief pause before serve
        self.rally_count = 0

    def update(self, dt):
        if not self.active:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.active = True
            return None

        # Movement
        self.rect.x += int(self.direction.x * self.speed * dt)
        self.rect.y += int(self.direction.y * self.speed * dt)

        # Wall collisions (Top & Bottom)
        if self.rect.top <= 0:
            self.rect.top = 0
            self.direction.y *= -1
            if self.sounds.get("wall"):
                self.sounds["wall"].play()
        elif self.rect.bottom >= WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT
            self.direction.y *= -1
            if self.sounds.get("wall"):
                self.sounds["wall"].play()

        # Paddle collisions
        for paddle in self.paddles:
            if self.rect.colliderect(paddle.rect):
                # Calculate bounce angle based on hit location
                offset = (self.rect.centery - paddle.rect.centery) / (paddle.rect.height / 2)
                offset = max(-0.9, min(0.9, offset))

                if paddle.is_player1 and self.direction.x > 0:
                    self.rect.right = paddle.rect.left
                    self.direction.x = -1
                    self.direction.y = offset
                    self.direction = self.direction.normalize()
                    self.speed = min(950, self.speed + 25)
                    self.rally_count += 1
                    if self.sounds.get("hit"):
                        self.sounds["hit"].play()

                elif not paddle.is_player1 and self.direction.x < 0:
                    self.rect.left = paddle.rect.right
                    self.direction.x = 1
                    self.direction.y = offset
                    self.direction = self.direction.normalize()
                    self.speed = min(950, self.speed + 25)
                    self.rally_count += 1
                    if self.sounds.get("hit"):
                        self.sounds["hit"].play()

        # Goal checks
        if self.rect.left <= 0:
            # Player 1 (Right) scores!
            if self.sounds.get("score"):
                self.sounds["score"].play()
            self.reset(serve_direction=-1)
            return "P1"

        elif self.rect.right >= WINDOW_WIDTH:
            # Player 2 (Left) scores!
            if self.sounds.get("score"):
                self.sounds["score"].play()
            self.reset(serve_direction=1)
            return "P2"

        return None


class PongDisplay:
    """
    Classic Retro Arcade Pong with Real Scoring & Persistent High Score.
    - Native 1280x720 canvas, centered within 1920x1080 overworld
    - Single player (AI-assisted Left paddle) or 2-player battle (W/S vs Arrows)
    - Persistent High Score saved to /Pong/highscore.txt
    - ESC returns smoothly to the overworld without crashing
    """
    def __init__(self, game_name="Pong"):
        self.game_name = game_name
        self.orig_width = WINDOW_WIDTH   # 1280
        self.orig_height = WINDOW_HEIGHT # 720
        self.game_surface = pygame.Surface((self.orig_width, self.orig_height))

        self.high_score = self.load_high_score()
        self.score_p1 = 0  # Right Player
        self.score_p2 = 0  # Left Player

        # Synthesized retro sound effects
        self.sounds = {
            "hit": make_beep(480, 0.08, volume=0.5),
            "wall": make_beep(260, 0.06, volume=0.35),
            "score": make_beep(880, 0.25, volume=0.6),
            "win": make_beep(660, 0.40, volume=0.5),
        }

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

    def run(self, screen):
        clock = pygame.time.Clock()

        # Reset scores for each fresh session
        self.score_p1 = 0
        self.score_p2 = 0

        # Fonts
        font_score = pygame.font.Font(None, 110)
        font_hud = pygame.font.Font(None, 40)
        font_sub = pygame.font.Font(None, 32)

        # Setup Paddles & Ball
        p1 = PongPaddle((WINDOW_WIDTH - 60, WINDOW_HEIGHT // 2), COLORS['paddle1'], is_player1=True)
        p2 = PongPaddle((60, WINDOW_HEIGHT // 2), COLORS['paddle2'], is_player1=False)

        all_sprites = pygame.sprite.Group()
        paddles = pygame.sprite.Group()

        paddles.add(p1, p2)
        all_sprites.add(p1, p2)

        ball = PongBall([p1, p2], self.sounds)
        all_sprites.add(ball)

        pos_x = (WIDTH - self.orig_width) // 2
        pos_y = (HEIGHT - self.orig_height) // 2

        running = True
        while running:
            dt = clock.tick(60) / 1000

            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    # Reset Match
                    if event.key == pygame.K_r:
                        self.score_p1 = 0
                        self.score_p2 = 0
                        ball.reset()

            # 2. Update Game
            p1.update(dt)
            p2.update(dt, ball=ball)
            goal = ball.update(dt)

            if goal == "P1":
                self.score_p1 += 1
                if self.score_p1 > self.high_score:
                    self.high_score = self.score_p1
                    self.save_high_score(self.high_score)

            elif goal == "P2":
                self.score_p2 += 1
                if self.score_p2 > self.high_score:
                    self.high_score = self.score_p2
                    self.save_high_score(self.high_score)

            # 3. Draw Court & Objects onto 1280x720 canvas
            self.game_surface.fill(COLORS['bg'])

            # Court Dividing Line (Dashed)
            center_x = WINDOW_WIDTH // 2
            dash_height = 18
            dash_gap = 14
            for y in range(0, WINDOW_HEIGHT, dash_height + dash_gap):
                pygame.draw.rect(self.game_surface, COLORS['center_line'], (center_x - 2, y, 4, dash_height))

            # Draw Paddles & Ball
            all_sprites.draw(self.game_surface)

            # 4. Scoreboard Display
            p2_surf = font_score.render(str(self.score_p2), True, COLORS['paddle2'])
            p1_surf = font_score.render(str(self.score_p1), True, COLORS['paddle1'])

            self.game_surface.blit(p2_surf, p2_surf.get_rect(center=(center_x - 140, 90)))
            self.game_surface.blit(p1_surf, p1_surf.get_rect(center=(center_x + 140, 90)))

            # High Score Banner in Middle
            hs_label = font_sub.render(f"PREVIOUS HIGH SCORE: {self.high_score}", True, (255, 215, 0))
            self.game_surface.blit(hs_label, hs_label.get_rect(center=(center_x, 30)))

            # Rally counter
            if ball.rally_count > 0:
                rally_text = font_sub.render(f"RALLY: {ball.rally_count}", True, (120, 160, 180))
                self.game_surface.blit(rally_text, rally_text.get_rect(center=(center_x, 150)))

            # Player Label hints
            p2_label = font_sub.render("P2 (W/S or AI)", True, (80, 120, 180))
            p1_label = font_sub.render("P1 (UP/DOWN)", True, (220, 100, 100))
            self.game_surface.blit(p2_label, (40, 20))
            self.game_surface.blit(p1_label, (WINDOW_WIDTH - p1_label.get_width() - 40, 20))

            # 5. Blit Centered on 1920x1080 Screen
            screen.fill((0, 0, 0))
            screen.blit(self.game_surface, (pos_x, pos_y))

            frame_rect = pygame.Rect(pos_x - 4, pos_y - 4, self.orig_width + 8, self.orig_height + 8)
            pygame.draw.rect(screen, (0, 255, 200), frame_rect, width=3, border_radius=6)

            hint = font_hud.render(
                "PONG  |  P1: Up/Down  |  P2: W/S (Auto AI if idle)  |  R: Reset Match  |  ESC: Exit",
                True,
                (180, 180, 200)
            )
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

            pygame.display.update()

