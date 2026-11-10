from control_hints import ControlHints
from arcade_screen import arcade_game_size, draw_arcade
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

WINDOW_WIDTH, WINDOW_HEIGHT = arcade_game_size(1280, 720)
PADDLE_SIZE = (30, 160)
BALL_SIZE = 26

COLORS = {
    'paddle1': '#ee322c',         # Red (Player 1 - Right)
    'paddle2': '#1d70d8',         # Blue (AI - Left)
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
        self.position_y = float(self.rect.centery)
        self.ai_speed = 440
        self.ai_reaction_timer = 0.0
        self.ai_target = float(WINDOW_HEIGHT / 2)
        self.ai_shot_error = 0.0
        self.ai_tracking_shot = False

    def ai_input(self, dt, ball):
        """Predict wall bounces, but react slowly and misjudge some returns."""
        incoming = ball.active and ball.direction.x < 0
        if incoming and not self.ai_tracking_shot:
            # Keep the same mistake throughout a shot; reroll on the next return.
            self.ai_shot_error = random.uniform(-45, 45)
            if random.random() < 0.18:
                self.ai_shot_error += random.choice((-1, 1)) * random.uniform(110, 180)
            self.ai_reaction_timer = random.uniform(0.16, 0.30)
        self.ai_tracking_shot = incoming
        self.ai_reaction_timer -= dt

        if self.ai_reaction_timer <= 0:
            self.ai_reaction_timer = random.uniform(0.12, 0.22)
            if incoming:
                velocity = ball.direction * ball.speed
                contact_x = self.rect.right + ball.rect.width / 2
                time_to_hit = max(0.0, (contact_x - ball.rect.centerx) / velocity.x)
                predicted_y = ball.rect.centery + velocity.y * time_to_hit

                # Fold the trajectory between the walls, allowing multiple bounces.
                radius = ball.rect.height / 2
                travel_height = WINDOW_HEIGHT - 2 * radius
                folded_y = (predicted_y - radius) % (2 * travel_height)
                intercept = radius + min(folded_y, 2 * travel_height - folded_y)
                self.ai_target = intercept + self.ai_shot_error
            else:
                # Recover toward center while the ball travels away or waits to serve.
                self.ai_target = WINDOW_HEIGHT / 2

            half_height = self.rect.height / 2
            self.ai_target = max(10 + half_height,
                                 min(WINDOW_HEIGHT - 10 - half_height, self.ai_target))

        diff = self.ai_target - self.position_y
        self.direction = 0 if abs(diff) <= 10 else (1 if diff > 0 else -1)

    def input(self, ball=None, dt=0.0):
        keys = pygame.key.get_pressed()
        if self.is_player1:
            # Player 1 controls the right paddle.
            self.direction = int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        else:
            self.direction = 0
            if ball is not None:
                self.ai_input(dt, ball)

    def update(self, dt, ball=None):
        self.input(ball, dt)
        speed = self.ai_speed if not self.is_player1 else self.speed
        movement = self.direction * speed * dt
        if not self.is_player1:
            # Stop at the target rather than oscillating around it.
            distance = self.ai_target - self.position_y
            movement = max(-abs(distance), min(abs(distance), movement))
        self.position_y += movement
        half_height = self.rect.height / 2
        self.position_y = max(10 + half_height,
                              min(WINDOW_HEIGHT - 10 - half_height, self.position_y))
        self.rect.centery = round(self.position_y)


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
        self.control_hints = ControlHints('pong')
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
            p2_label = font_sub.render("AI", True, (80, 120, 180))
            p1_label = font_sub.render("YOU (UP/DOWN)", True, (220, 100, 100))
            self.game_surface.blit(p2_label, (40, 20))
            self.game_surface.blit(p1_label, (WINDOW_WIDTH - p1_label.get_width() - 40, 20))

            # 5. Blit Centered on 1920x1080 Screen
            screen.fill((0, 0, 0))
            draw_arcade(screen, self.game_surface)


            self.control_hints.draw(screen)

            pygame.display.update()

