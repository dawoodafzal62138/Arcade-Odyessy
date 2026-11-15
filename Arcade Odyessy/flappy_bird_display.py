from control_hints import ControlHints
from arcade_screen import game_ticks, arcade_game_size, draw_arcade, arcade_mouse
import os
import sys
import random
from pathlib import Path
import pygame
from settigns import WIDTH, HEIGHT, CURRENT_DIR

# =========================================================================
# FLAPPY BIRD GAME (Expanded cabinet playfield)
# =========================================================================
FLAPPY_BASE = str((CURRENT_DIR.parent / "Flappy-Bird-Game-main").resolve())
RESOURCE_DIR = os.path.join(FLAPPY_BASE, "resourse_flappy")
FLAPPY_HIGHSCORE_PATH = os.path.join(FLAPPY_BASE, "highscore.txt")

GAME_WIDTH, GAME_HEIGHT = arcade_game_size(450, 600)


class FlappyBirdDisplay:
    """
    Flappy Bird Game Display (Expanded cabinet playfield)
    - Full authentic mechanics, pipe generation, physics, animations, and sound effects
    - Uses a wider native canvas matching the cabinet screen
    - Overworld is completely stopped while playing
    - ESC returns smoothly to the overworld without crashing
    """
    def __init__(self, game_name="Flappy-Bird-Game-main"):
        self.game_name = game_name
        self.orig_width = GAME_WIDTH   # 450
        self.orig_height = GAME_HEIGHT # 600
        self.game_surface = pygame.Surface((self.orig_width, self.orig_height))
        self.assets_loaded = False
        self.high_score = self._load_high_score()

    def _load_high_score(self):
        try:
            if os.path.exists(FLAPPY_HIGHSCORE_PATH):
                with open(FLAPPY_HIGHSCORE_PATH, "r") as f:
                    return int(f.read().strip())
        except Exception:
            pass
        return 0

    def _save_high_score(self, score):
        try:
            with open(FLAPPY_HIGHSCORE_PATH, "w") as f:
                f.write(str(score))
        except Exception:
            pass

    def _init_assets(self):
        if self.assets_loaded:
            return

        img_dir = os.path.join(RESOURCE_DIR, "images")
        music_dir = os.path.join(RESOURCE_DIR, "music")

        # Bird animation frames
        b0 = pygame.image.load(os.path.join(img_dir, "bird", "flappybird0.png")).convert_alpha()
        b1 = pygame.image.load(os.path.join(img_dir, "bird", "flappybird1.png")).convert_alpha()
        b2 = pygame.image.load(os.path.join(img_dir, "bird", "flappybird2.png")).convert_alpha()
        b3 = pygame.image.load(os.path.join(img_dir, "bird", "flappybird3.png")).convert_alpha()

        self.bird_surfaces = [
            pygame.transform.scale(b0, (55, 40)),
            pygame.transform.scale(b1, (55, 40)),
            pygame.transform.scale(b2, (55, 40)),
            pygame.transform.scale(b3, (55, 40)),
        ]

        # Pipes
        pipeup_raw = pygame.image.load(os.path.join(img_dir, "pipes", "toppipe.png")).convert_alpha()
        pipedown_raw = pygame.image.load(os.path.join(img_dir, "pipes", "bottompipe.png")).convert_alpha()
        self.pipeup_surface = pygame.transform.scale(pipeup_raw, (70, 1000))
        self.pipedown_surface = pygame.transform.scale(pipedown_raw, (70, 1000))

        # UI & Background
        font_path = os.path.join(RESOURCE_DIR, "04B_19__.TTF")
        self.font1 = pygame.font.Font(font_path, 50) if os.path.exists(font_path) else pygame.font.Font(None, 50)
        self.font2 = pygame.font.Font(font_path, 35) if os.path.exists(font_path) else pygame.font.Font(None, 35)

        flappy_logo = pygame.image.load(os.path.join(img_dir, "flappybird.png")).convert_alpha()
        self.flappybird_image = pygame.transform.scale(flappy_logo, (400, 130))
        self.flappybird_image_rect = self.flappybird_image.get_rect(center=(GAME_WIDTH // 2, 150))

        btn = pygame.image.load(os.path.join(img_dir, "button_play.png")).convert_alpha()
        self.button_image = pygame.transform.scale(btn, (100, 100))
        self.button_rect = self.button_image.get_rect(center=(GAME_WIDTH // 2, 300))

        bg = pygame.image.load(os.path.join(img_dir, "bird", "background.png")).convert_alpha()
        background_tile = pygame.transform.scale(bg, (450, 300))
        self.background_image = pygame.Surface((GAME_WIDTH, 300))
        for x in range(0, GAME_WIDTH, background_tile.get_width()):
            self.background_image.blit(background_tile, (x, 0))
        self.background_image_rect = self.background_image.get_rect(center=(GAME_WIDTH // 2, 450))

        gameover_raw = pygame.image.load(os.path.join(img_dir, "gameover.png")).convert()
        self.gameover_image = gameover_raw
        self.gameover_image_rect = self.gameover_image.get_rect(center=(GAME_WIDTH // 2, 150))

        # Audio
        self.background_sound = pygame.mixer.Sound(os.path.join(music_dir, "bgm_mario.mp3"))
        self.die_sound = pygame.mixer.Sound(os.path.join(music_dir, "sfx_die.wav"))
        self.hit_sound = pygame.mixer.Sound(os.path.join(music_dir, "sfx_hit.wav"))
        self.point_sound = pygame.mixer.Sound(os.path.join(music_dir, "sfx_point.wav"))
        self.jump_sound = pygame.mixer.Sound(os.path.join(music_dir, "sfx_wing.wav"))

        self.background_sound.set_volume(0.3)
        self.jump_sound.set_volume(0.5)
        self.point_sound.set_volume(0.7)

        self.assets_loaded = True

    def create_pipe_pair(self):
        gap = 200
        gap_center = random.randint(150, 450)
        pipeup_rect = self.pipeup_surface.get_rect(midbottom=(GAME_WIDTH + 50, gap_center - (gap / 2)))
        pipedown_rect = self.pipedown_surface.get_rect(midtop=(GAME_WIDTH + 50, gap_center + (gap / 2)))
        return pipeup_rect, pipedown_rect

    def run(self, screen):
        self.control_hints = ControlHints('flappy_bird')
        self._init_assets()
        clock = pygame.time.Clock()
        hud_font = pygame.font.Font(None, 36)

        pos_x = (WIDTH - self.orig_width) // 2
        pos_y = (HEIGHT - self.orig_height) // 2

        # Game state variables
        game_active = False
        pipes = []
        score = 0
        event_input = True
        bird_hit = False
        show_gameover_screen = False

        bird_gravity = 0
        bird_surface_index = 0
        bird_surface_image = self.bird_surfaces[bird_surface_index]
        bird_rect = bird_surface_image.get_rect(midbottom=(80, 200))

        # Pipe spawn timer (every 2 seconds)
        pipe_timer = 0
        pipe_interval = 2000

        try:
            self.background_sound.play(loops=-1)
        except Exception:
            pass

        running = True
        while running:
            dt = clock.tick(60)

            # -------------------------------------------------------------
            # EVENT HANDLING
            # -------------------------------------------------------------
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    # Space or Return to flap or start
                    if event.key in (pygame.K_SPACE, pygame.K_UP):
                        if game_active and event_input:
                            bird_gravity = -9
                            self.jump_sound.play()
                        elif not game_active:
                            game_active = True
                            bird_gravity = -9
                            score = 0
                            pipes.clear()
                            bird_rect.y = 200
                            show_gameover_screen = False

                    elif event.key == pygame.K_RETURN and not game_active:
                        game_active = True
                        bird_gravity = -9
                        score = 0
                        pipes.clear()
                        bird_rect.y = 200
                        show_gameover_screen = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    local_pos = arcade_mouse(screen, event.pos, self.game_surface.get_size())
                    if game_active and event_input:
                        bird_gravity = -9
                        self.jump_sound.play()
                    elif not game_active:
                        if self.button_rect.collidepoint(local_pos):
                            game_active = True
                            bird_gravity = -9
                            score = 0
                            pipes.clear()
                            bird_rect.y = 200
                            show_gameover_screen = False

            # -------------------------------------------------------------
            # GAMEPLAY LOOP
            # -------------------------------------------------------------
            if game_active:
                self.game_surface.fill((139, 212, 245))
                self.game_surface.blit(self.background_image, self.background_image_rect)

                # Animate bird
                bird_surface_index += 0.15
                if bird_surface_index >= len(self.bird_surfaces):
                    bird_surface_index = 0
                bird_surface_image = self.bird_surfaces[int(bird_surface_index)]

                rotated_bird = pygame.transform.rotozoom(bird_surface_image, -bird_gravity * 3, 1)
                new_bird_rect = rotated_bird.get_rect(center=bird_rect.center)
                self.game_surface.blit(rotated_bird, new_bird_rect)

                # Draw pipes
                for pipe in pipes:
                    if pipe.bottom >= GAME_HEIGHT:
                        self.game_surface.blit(self.pipedown_surface, pipe)
                    else:
                        self.game_surface.blit(self.pipeup_surface, pipe)

                # Apply physics
                bird_gravity += 0.6
                bird_rect.y += bird_gravity

                # Spawn pipes
                if not bird_hit:
                    pipe_timer += dt
                    if pipe_timer >= pipe_interval:
                        pipe_timer = 0
                        pipes.extend(self.create_pipe_pair())

                    # Move pipes & check score
                    for pipe in pipes:
                        pipe.x -= 4
                        if 48 < pipe.centerx <= 52:
                            score += 0.5
                            self.point_sound.play()
                    pipes = [pipe for pipe in pipes if pipe.x > -100]

                    # Check collisions
                    hit = False
                    for pipe in pipes:
                        if bird_rect.colliderect(pipe):
                            hit = True
                            break
                    if bird_rect.top <= -50 or bird_rect.bottom >= GAME_HEIGHT:
                        hit = True

                    if hit:
                        bird_hit = True
                        self.hit_sound.play()
                        event_input = False
                        # If bird flew out the top, nudge it back so it falls down
                        if bird_rect.top <= -50:
                            bird_rect.top = 0
                            bird_gravity = max(bird_gravity, 1)  # Ensure it falls

                # Handle falling after hit
                if bird_hit and bird_rect.bottom >= GAME_HEIGHT:
                    bird_hit = False
                    self.die_sound.play()
                    game_active = False
                    event_input = True
                    show_gameover_screen = True
                    # Update & persist high score
                    final_score = int(score)
                    if final_score > self.high_score:
                        self.high_score = final_score
                        self._save_high_score(self.high_score)

                # Draw Score
                score_surf = self.font1.render(str(int(score)), True, (255, 255, 255))
                score_shadow = self.font1.render(str(int(score)), True, (0, 0, 0))
                score_rect = score_surf.get_rect(center=(GAME_WIDTH // 2, 50))
                self.game_surface.blit(score_shadow, score_rect.move(2, 2))
                self.game_surface.blit(score_surf, score_rect)

            else:
                # Menu / Game Over Screen
                pipes.clear()
                bird_rect.y = 200
                self.game_surface.fill((139, 212, 245))

                if not show_gameover_screen:
                    self.game_surface.blit(self.flappybird_image, self.flappybird_image_rect)
                    self.game_surface.blit(self.background_image, self.background_image_rect)
                    self.game_surface.blit(self.button_image, self.button_rect)
                else:
                    self.game_surface.blit(self.gameover_image, self.gameover_image_rect)
                    self.game_surface.blit(self.background_image, self.background_image_rect)
                    self.game_surface.blit(self.button_image, self.button_rect)

                    gameover_score = self.font2.render(f"Score: {int(score)}", True, (0, 0, 0))
                    gameover_score_rect = gameover_score.get_rect(center=(GAME_WIDTH // 2, 430))
                    self.game_surface.blit(gameover_score, gameover_score_rect)

                    # High score
                    hs_surf = self.font2.render(f"Best: {self.high_score}", True, (255, 200, 0))
                    self.game_surface.blit(hs_surf, hs_surf.get_rect(center=(GAME_WIDTH // 2, 460)))

                play_hint = self.font2.render("Press SPACE to Play", True, (255, 255, 255))
                play_hint_rect = play_hint.get_rect(center=(GAME_WIDTH // 2, 490))
                self.game_surface.blit(self.font2.render("Press SPACE to Play", True, (0, 0, 0)), play_hint_rect.move(2, 2))
                self.game_surface.blit(play_hint, play_hint_rect)

            # -------------------------------------------------------------
            # BLIT CENTERED ON 1920x1080 SCREEN
            # -------------------------------------------------------------
            screen.fill((0, 0, 0))
            draw_arcade(screen, self.game_surface, clock=clock)


            self.control_hints.draw(screen)

            pygame.display.update()

        # Stop audio upon returning to overworld
        try:
            self.background_sound.stop()
        except Exception:
            pass

