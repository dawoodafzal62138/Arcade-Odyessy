from control_hints import ControlHints
from arcade_screen import cover_background, arcade_game_size, draw_arcade, NinjaArcadeScreen
import os
import sys
import math
import random
from pathlib import Path
import pygame
from settigns import WIDTH, HEIGHT, CURRENT_DIR

# -------------------------------------------------------------------------
# IMPORT ESSENTIAL FUNCTIONS & MODULES FROM NINJA GAME
# -------------------------------------------------------------------------
NINJA_BASE = str((CURRENT_DIR.parent / "ninja_game").resolve())
if NINJA_BASE not in sys.path:
    sys.path.insert(0, NINJA_BASE)

from scripts.sparks import Sparks  # type: ignore
from scripts.particles import Particles  # type: ignore
from scripts.utilities import load_image, load_images, Animations  # type: ignore
from scripts.entities import Player as NinjaPlayer, Enemy as NinjaEnemy, PhysicsEntity as NinjaPhysicsEntity  # type: ignore
from scripts.tilemap import Tilemap as NinjaTilemap  # type: ignore
from scripts.clouds import Clouds as NinjaClouds  # type: ignore


class CallableRect(pygame.Rect):
    """Permissive Rect that works seamlessly whether invoked as rect() or rect."""
    def __call__(self):
        return self


class RectProperty:
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return CallableRect(int(instance.pos[0]), int(instance.pos[1]), int(instance.size[0]), int(instance.size[1]))


NinjaPhysicsEntity.rect = RectProperty()
NinjaPlayer.rect = RectProperty()
NinjaEnemy.rect = RectProperty()


# =========================================================================
# NINJA GAME DISPLAY (Playfield fitted to the version 2 cabinet)
# =========================================================================
class NinjaDisplay:
    def __init__(self, game_name="ninja_game"):
        self.game_name = game_name
        self.orig_width, self.orig_height = arcade_game_size(640, 480, NinjaArcadeScreen)
        self.game_surface = pygame.Surface((self.orig_width, self.orig_height))
        self.display = pygame.Surface((self.orig_width // 2, self.orig_height // 2), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((self.orig_width // 2, self.orig_height // 2))
        self.movement = [False, False]

        self.assets = {
            'decor': load_images('/tiles/decor'),
            'grass': load_images('/tiles/grass'),
            'large_decor': load_images('/tiles/large_decor'),
            'stone': load_images('/tiles/stone'),
            'player': load_image('/entities/player.png'),
            'background': load_image('/background.png'),
            'clouds': load_images('/clouds'),
            'player_idle': Animations(load_images('/entities/player/idle'), image_dur=6),
            'player_run': Animations(load_images('/entities/player/run'), image_dur=4),
            'player_jump': Animations(load_images('/entities/player/jump')),
            'player_slide': Animations(load_images('/entities/player/slide')),
            'player_wall_slide': Animations(load_images('/entities/player/wall_slide')),
            'particles_leaf': Animations(load_images('/particles/leaf'), image_dur=20, loop=False),
            'particles_particle': Animations(load_images('/particles/particle'), image_dur=6, loop=False),
            'spawners': load_images('/tiles/spawners'),
            'enemy_idle': Animations(load_images('/entities/enemy/idle'), image_dur=6),
            'enemy_run': Animations(load_images('/entities/enemy/run'), image_dur=4),
            'gun': load_image('/gun.png'),
            'projectile': load_image('/projectile.png'),
        }

        self.background = cover_background(self.assets['background'], self.display_2.get_size())

        self.sounds = {
            "jump": pygame.mixer.Sound(f"{NINJA_BASE}/data/sfx/jump.wav"),
            "shoot": pygame.mixer.Sound(f"{NINJA_BASE}/data/sfx/shoot.wav"),
            "hit": pygame.mixer.Sound(f"{NINJA_BASE}/data/sfx/hit.wav"),
            "dash": pygame.mixer.Sound(f"{NINJA_BASE}/data/sfx/dash.wav"),
            "ambience": pygame.mixer.Sound(f"{NINJA_BASE}/data/sfx/ambience.wav"),
        }
        self.sounds["ambience"].set_volume(0.2)
        self.sounds["shoot"].set_volume(0.4)
        self.sounds["hit"].set_volume(0.8)
        self.sounds["dash"].set_volume(0.3)
        self.sounds["jump"].set_volume(0.7)

        try:
            pygame.mixer.music.load(f"{NINJA_BASE}/data/music.wav")
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
            self.sounds["ambience"].play(-1)
        except Exception:
            pass

        self.clouds = NinjaClouds(self.assets["clouds"], count=16)
        self.player = NinjaPlayer(self, (50, 50), (8, 15))
        self.tilemap = NinjaTilemap(self, tile_size=16)

        self.scroll = [0, 0]
        self.render_scroll = (0, 0)
        self.level = 0
        self.load_level(self.level)

    def load_level(self, map_id):
        self.tilemap.load(f"{NINJA_BASE}/data/maps/{map_id}.json")
        self.leaf_spawners = []
        for tree in self.tilemap.extract_tiles([("large_decor", 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 18))

        self.particles = []
        self.enemies = []
        self.projectiles = []
        self.sparks = []
        for spawner in self.tilemap.extract_tiles([("spawners", 0), ("spawners", 1)], keep=False):
            if spawner["variant"] == 0:
                self.player.pos = spawner["pos"]
                self.player.airtime = 0
            else:
                self.enemies.append(NinjaEnemy(self, spawner["pos"], (8, 15)))

        self.dead = 0
        self.screenshake = 0
        self.transition = -30

    def run(self, screen):
        self.control_hints = ControlHints('ninja')
        clock = pygame.time.Clock()
        running = True
        hud_font = pygame.font.Font(None, 36)

        while running:
            dt = clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        try:
                            pygame.mixer.music.stop()
                            self.sounds["ambience"].stop()
                        except Exception:
                            pass
                    if event.key in (pygame.K_LEFT, pygame.K_a): self.movement[0] = True
                    if event.key in (pygame.K_RIGHT, pygame.K_d): self.movement[1] = True
                    if event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                        if self.player.jump(): self.sounds["jump"].play(0)
                    if event.key == pygame.K_x: self.player.dash()

                elif event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LEFT, pygame.K_a): self.movement[0] = False
                    if event.key in (pygame.K_RIGHT, pygame.K_d): self.movement[1] = False

            # Update
            self.screenshake = max(0, self.screenshake - 1)
            if self.dead:
                self.dead += 1
                if self.dead >= 10: self.transition = min(self.transition + 1, 30)
                if self.dead > 40: self.load_level(self.level)

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    maps_dir = os.path.join(NINJA_BASE, "data", "maps")
                    map_count = len(os.listdir(maps_dir)) if os.path.exists(maps_dir) else 1
                    self.level = min(self.level + 1, map_count - 1)
                    self.load_level(self.level)

            if self.transition < 0: self.transition += 1

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() // 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() // 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            for rect in self.leaf_spawners:
                if random.random() * 30000 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particles(self, "leaf", pos, velocity=[-0.2, 0.6], frame=random.randint(0, 17)))

            self.clouds.update()
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                if kill:
                    self.enemies.remove(enemy)
                    self.sounds["hit"].play(0)

            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))

            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for _ in range(4):
                        self.sparks.append(Sparks(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.sounds["hit"].play(0)
                        self.screenshake = max(self.screenshake, 16)
                        p_center = self.player.rect.center
                        for _ in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(Sparks(p_center, angle, 2 + random.random()))
                            self.particles.append(Particles(self, 'particle', p_center,
                                                            velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5],
                                                            frame=random.randint(0, 7)))

            for spark in self.sparks.copy():
                if spark.update(): self.sparks.remove(spark)

            for particle in self.particles.copy():
                if particle.update(): self.particles.remove(particle)
                elif particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3

            # Draw
            self.display.fill((0, 0, 0, 0))
            self.display_2.fill((0, 0, 0))
            self.display_2.blit(self.background, (0, 0))
            self.clouds.render(self.display_2, offset=render_scroll)
            self.tilemap.render(self.display, offset=render_scroll)

            for enemy in self.enemies: enemy.render(self.display, offset=render_scroll)
            if not self.dead: self.player.render(self.display, offset=render_scroll)

            for projectile in self.projectiles:
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0],
                                        projectile[0][1] - img.get_height() / 2 - render_scroll[1]))

            for spark in self.sparks: spark.render(self.display, offset=render_scroll)
            for particle in self.particles: particle.render(self.display, offset=render_scroll)

            display_mask = pygame.mask.from_surface(self.display)
            display_mask_outline = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                self.display_2.blit(display_mask_outline, offset)

            if self.transition:
                transition_surface = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surface, (255, 255, 255),
                                   (self.display.get_width() // 2, self.display.get_height() // 2),
                                   (30 - abs(self.transition)) * 8)
                transition_surface.set_colorkey((255, 255, 255))
                self.display.blit(transition_surface, (0, 0))

            self.display_2.blit(self.display, (0, 0))
            pygame.transform.scale(self.display_2, (self.orig_width, self.orig_height), self.game_surface)

            # Center on 1920x1080 screen
            screen.fill((0, 0, 0))
            shake_x = random.randint(-self.screenshake, self.screenshake) if self.screenshake > 0 else 0
            shake_y = random.randint(-self.screenshake, self.screenshake) if self.screenshake > 0 else 0
            pos_x = (WIDTH - self.orig_width) // 2 + shake_x
            pos_y = (HEIGHT - self.orig_height) // 2 + shake_y
            draw_arcade(screen, self.game_surface, (shake_x, shake_y), NinjaArcadeScreen)


            self.control_hints.draw(screen)

            pygame.display.update()

