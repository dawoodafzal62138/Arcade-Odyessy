from control_hints import ControlHints
from arcade_screen import arcade_game_size, draw_arcade, arcade_mouse
import os
import sys
import math
import random
from random import randint, uniform
from pathlib import Path
import pygame
from settigns import WIDTH, HEIGHT, CURRENT_DIR

# =========================================================================
# SPACE SHOOTER (Native 1280x720 resolution)
# Completely self-contained to avoid namespace collisions with Arcade Odyssey
# =========================================================================
SPACE_BASE = str((CURRENT_DIR.parent / "space shooter").resolve())
HIGHSCORE_PATH = os.path.join(SPACE_BASE, "highscore.txt")

GAME_WIDTH, GAME_HEIGHT = arcade_game_size(1280, 720)


def meteor_spawn_interval(score):
    """Spawn faster with the current run's score, bounded at 100 ms."""
    return max(100, 450 / (1 + max(0, score) / 200))


def s_join(*args):
    return os.path.join(SPACE_BASE, *args)


class SpacePlayer(pygame.sprite.Sprite):
    def __init__(self, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center=(GAME_WIDTH / 2, GAME_HEIGHT / 2))
        self.mask = pygame.mask.from_surface(self.image)
        self.player_speed = 600
        self.can_shoot = True
        self.last_shoot_time = 0
        self.cooldown_time = 200

    def laser_timer(self):
        if not self.can_shoot:
            now = pygame.time.get_ticks()
            if now - self.last_shoot_time > self.cooldown_time:
                self.can_shoot = True

    def update(self, dt, local_mouse=None, mouse_moved=False):
        keys = pygame.key.get_pressed()
        dx = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = int(keys[pygame.K_DOWN] or keys[pygame.K_s]) - int(keys[pygame.K_UP] or keys[pygame.K_w])

        # If keyboard moved, use keyboard; if mouse moved and no keyboard, use mouse
        if dx != 0 or dy != 0:
            move_vec = pygame.math.Vector2(dx, dy)
            if move_vec.length() > 0:
                move_vec = move_vec.normalize()
            self.rect.center += move_vec * self.player_speed * dt
        elif mouse_moved and local_mouse is not None:
            self.rect.center = (local_mouse[0], local_mouse[1])

        # Boundaries
        if self.rect.top < 20:
            self.rect.top = 20
        if self.rect.bottom > GAME_HEIGHT - 20:
            self.rect.bottom = GAME_HEIGHT - 20
        if self.rect.left < 20:
            self.rect.left = 20
        if self.rect.right > GAME_WIDTH - 20:
            self.rect.right = GAME_WIDTH - 20

        self.laser_timer()


class SpaceStar(pygame.sprite.Sprite):
    def __init__(self, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center=(randint(1, GAME_WIDTH), randint(1, GAME_HEIGHT)))


class SpaceLaser(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(midbottom=pos)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.rect.y -= int(650 * dt)
        if self.rect.bottom < -20:
            self.kill()


class SpaceMeteor(pygame.sprite.Sprite):
    def __init__(self, surf, pos, groups):
        super().__init__(groups)
        self.original_surface = surf
        self.image = surf
        self.rect = self.image.get_frect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.start_time = pygame.time.get_ticks()
        self.lifetime = 4500
        self.direction = pygame.math.Vector2(uniform(-0.4, 0.4), 1)
        self.speed = randint(300, 480)
        self.rotation_speed = randint(40, 120)
        self.rotation_angle = 0

    def update(self, dt):
        self.rect.center += self.speed * self.direction * dt
        if pygame.time.get_ticks() - self.start_time > self.lifetime or self.rect.top > GAME_HEIGHT + 100:
            self.kill()

        self.rotation_angle += self.rotation_speed * dt
        self.image = pygame.transform.rotozoom(self.original_surface, self.rotation_angle, 1)
        self.rect = self.image.get_frect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)


class SpaceExplosion(pygame.sprite.Sprite):
    def __init__(self, frames, pos, groups):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(center=pos)

    def update(self, dt):
        self.frame_index += 25 * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
            self.rect = self.image.get_frect(center=self.rect.center)
        else:
            self.kill()


class SpaceShooterDisplay:
    """
    Space Shooter Game Display (Native 1280x720 resolution)
    - Full authentic meteor physics, rotation, lasers, animations, sound effects
    - Working collision logic: Laser vs Meteor (explosions & points), Player vs Meteor (Game Over)
    - Persistent High Score saved to /space shooter/highscore.txt
    - Runs inside its exact 1280x720 canvas, centered within the 1920x1080 overworld
    - Overworld is completely stopped while playing
    - ESC returns smoothly to the overworld without crashing
    """
    def __init__(self, game_name="space shooter"):
        self.game_name = game_name
        self.orig_width = GAME_WIDTH   # 1280
        self.orig_height = GAME_HEIGHT # 720
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

        img_dir = s_join("images")
        audio_dir = s_join("audio")

        # Images
        self.player_surface = pygame.image.load(os.path.join(img_dir, "player.png")).convert_alpha()
        self.star_surface = pygame.image.load(os.path.join(img_dir, "star.png")).convert_alpha()
        self.meteor_surface = pygame.image.load(os.path.join(img_dir, "meteor.png")).convert_alpha()
        self.laser_surface = pygame.image.load(os.path.join(img_dir, "laser.png")).convert_alpha()

        # Explosion frames (21 frames)
        self.explosion_frames = []
        for i in range(21):
            frame_path = os.path.join(img_dir, "explosion", f"{i}.png")
            if os.path.exists(frame_path):
                self.explosion_frames.append(pygame.image.load(frame_path).convert_alpha())

        # Fonts
        font_path = os.path.join(img_dir, "Oxanium-Bold.ttf")
        self.font = pygame.font.Font(font_path, 40) if os.path.exists(font_path) else pygame.font.Font(None, 40)
        self.font_big = pygame.font.Font(font_path, 80) if os.path.exists(font_path) else pygame.font.Font(None, 80)
        self.font_sub = pygame.font.Font(font_path, 32) if os.path.exists(font_path) else pygame.font.Font(None, 32)

        # Audio
        self.laser_sound = pygame.mixer.Sound(os.path.join(audio_dir, "laser.wav"))
        self.laser_sound.set_volume(0.5)

        self.explosion_sound = pygame.mixer.Sound(os.path.join(audio_dir, "explosion.wav"))
        self.explosion_sound.set_volume(0.6)

        damage_path = os.path.join(audio_dir, "damage.ogg")
        self.damage_sound = pygame.mixer.Sound(damage_path) if os.path.exists(damage_path) else self.explosion_sound
        self.damage_sound.set_volume(0.6)

        self.game_music = pygame.mixer.Sound(os.path.join(audio_dir, "game_music.wav"))
        self.game_music.set_volume(0.35)

        self.assets_loaded = True

    def run(self, screen):
        self.control_hints = ControlHints('space_shooter')
        self._init_assets()
        clock = pygame.time.Clock()
        hud_font = pygame.font.Font(None, 36)

        pos_x = (WIDTH - self.orig_width) // 2
        pos_y = (HEIGHT - self.orig_height) // 2

        try:
            self.game_music.play(loops=-1)
        except Exception:
            pass

        running_session = True
        while running_session:
            # Sprite groups
            all_sprites = pygame.sprite.Group()
            meteor_sprites = pygame.sprite.Group()
            laser_sprites = pygame.sprite.Group()

            # Background stars
            for _ in range(25):
                SpaceStar(self.star_surface, all_sprites)

            # Player
            player = SpacePlayer(self.player_surface, all_sprites)

            score = 0
            start_ticks = pygame.time.get_ticks()
            meteor_timer = 0

            game_active = True
            game_over = False
            last_mouse_pos = pygame.mouse.get_pos()

            while game_active:
                dt = clock.tick(60) / 1000
                raw_mouse = pygame.mouse.get_pos()
                local_mouse = arcade_mouse(screen, raw_mouse, self.game_surface.get_size())
                mouse_moved = (raw_mouse != last_mouse_pos)
                last_mouse_pos = raw_mouse

                # -------------------------------------------------------------
                # 1. EVENT HANDLING
                # -------------------------------------------------------------
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        try:
                            self.game_music.stop()
                        except Exception:
                            pass
                        return

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            try:
                                self.game_music.stop()
                            except Exception:
                                pass
                            return

                    # Left Click to Shoot (single-click handled by held-fire block below)
                    # Note: continuous fire is handled after the event loop via held-fire check

                # Continuous fire if holding Left Click or Space
                mouse_buttons = pygame.mouse.get_pressed()
                held_keys = pygame.key.get_pressed()
                if (mouse_buttons[0] or held_keys[pygame.K_SPACE]) and player.can_shoot:
                    SpaceLaser(self.laser_surface, player.rect.midtop, (all_sprites, laser_sprites))
                    if self.laser_sound:
                        self.laser_sound.play()
                    player.can_shoot = False
                    player.last_shoot_time = pygame.time.get_ticks()

                # -------------------------------------------------------------
                # 2. METEOR SPAWNING
                # -------------------------------------------------------------
                survival_time = (pygame.time.get_ticks() - start_ticks) // 1000
                # Double the starting density at 200 points, up to 10 per second.
                meteor_interval = meteor_spawn_interval(score + survival_time)
                meteor_timer += dt * 1000
                if meteor_timer >= meteor_interval:
                    meteor_timer %= meteor_interval
                    spawn_x = randint(30, GAME_WIDTH - 30)
                    spawn_y = randint(-150, -50)
                    SpaceMeteor(self.meteor_surface, (spawn_x, spawn_y), (all_sprites, meteor_sprites))

                # -------------------------------------------------------------
                # 3. UPDATES
                # -------------------------------------------------------------
                player.update(dt, local_mouse=local_mouse, mouse_moved=mouse_moved)
                for sprite in list(all_sprites):
                    if sprite != player:
                        sprite.update(dt)

                # -------------------------------------------------------------
                # 4. COLLISION LOGIC
                # -------------------------------------------------------------
                # Laser vs Meteor collisions
                for l in list(laser_sprites):
                    collided_meteors = pygame.sprite.spritecollide(l, meteor_sprites, True, pygame.sprite.collide_mask)
                    if collided_meteors:
                        if self.explosion_sound:
                            self.explosion_sound.play()
                        if self.explosion_frames:
                            SpaceExplosion(self.explosion_frames, l.rect.midtop, all_sprites)
                        l.kill()
                        score += 10
                        if score > self.high_score:
                            self.high_score = score
                            self.save_high_score(self.high_score)

                # Player vs Meteor collisions
                player_hit = pygame.sprite.spritecollide(player, meteor_sprites, True, pygame.sprite.collide_mask)
                if player_hit:
                    if self.damage_sound:
                        self.damage_sound.play()
                    if self.explosion_frames:
                        SpaceExplosion(self.explosion_frames, player.rect.center, all_sprites)
                    player.kill()
                    game_active = False
                    game_over = True

                # Score based on survival time (+1 pt / sec)
                survival_time = (pygame.time.get_ticks() - start_ticks) // 1000
                total_display_score = score + survival_time

                if total_display_score > self.high_score:
                    self.high_score = total_display_score
                    self.save_high_score(self.high_score)

                # -------------------------------------------------------------
                # 5. DRAW TO 1280x720 CANVAS
                # -------------------------------------------------------------
                self.game_surface.fill("#3b2749")
                all_sprites.draw(self.game_surface)

                # Score Display Box (Retro Style)
                score_str = f"SCORE: {total_display_score}"
                font_surf = self.font.render(score_str, True, (240, 240, 240))
                font_rect = font_surf.get_frect(midbottom=(GAME_WIDTH / 2, GAME_HEIGHT - 35))
                self.game_surface.blit(font_surf, font_rect)
                pygame.draw.rect(self.game_surface, (240, 240, 240), font_rect.inflate(24, 12).move(0, -6), 4, 8)

                # High Score Display on Top
                hs_surf = self.font_sub.render(f"HIGH SCORE: {self.high_score}", True, (255, 215, 0))
                self.game_surface.blit(hs_surf, hs_surf.get_frect(center=(GAME_WIDTH / 2, 30)))

                # -------------------------------------------------------------
                # 6. BLIT CENTERED ON 1920x1080 SCREEN
                # -------------------------------------------------------------
                screen.fill((0, 0, 0))
                draw_arcade(screen, self.game_surface)


                self.control_hints.draw(screen)

                pygame.display.update()

            # -------------------------------------------------------------
            # GAME OVER SCREEN
            # -------------------------------------------------------------
            if game_over:
                # Let explosion animation finish on screen
                for _ in range(30):
                    clock.tick(60)
                    all_sprites.update(1 / 60)
                    self.game_surface.fill("#3b2749")
                    all_sprites.draw(self.game_surface)
                    draw_arcade(screen, self.game_surface)
                    pygame.display.update()

                restart = self._show_game_over(screen, total_display_score, pos_x, pos_y)
                if not restart:
                    try:
                        self.game_music.stop()
                    except Exception:
                        pass
                    return

    def _show_game_over(self, screen, final_score, pos_x, pos_y):
        """Displays Game Over on the 1280x720 canvas."""
        self.game_surface.fill((30, 15, 35))

        t1 = self.font_big.render("GAME OVER", True, (255, 70, 90))
        t2 = self.font.render(f"Final Score: {final_score}", True, (240, 240, 255))
        t3 = self.font_sub.render(f"High Score: {self.high_score}", True, (255, 215, 0))
        t4 = self.font_sub.render("Press ENTER to Play Again  |  ESC to Return to Overworld", True, (180, 180, 220))

        self.game_surface.blit(t1, t1.get_frect(center=(GAME_WIDTH // 2, 230)))
        self.game_surface.blit(t2, t2.get_frect(center=(GAME_WIDTH // 2, 330)))
        self.game_surface.blit(t3, t3.get_frect(center=(GAME_WIDTH // 2, 400)))
        self.game_surface.blit(t4, t4.get_frect(center=(GAME_WIDTH // 2, 500)))

        screen.fill((0, 0, 0))
        draw_arcade(screen, self.game_surface)

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
        return False
