from settigns import *
from All_sprite import AllSprites
from atmosphere import Atmosphere
import pytmx 
from sprite import Player, CollisionSprites, Sprite
from utils import *
from displays import get_display
import pygame
import sys
import math


class Game:
    def __init__(self):
        pygame.init()
        # Fullscreen 1920x1080 without pygame.SCALED
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Arcade Odyssey")
        self.clock = pygame.time.Clock()
        self.Running = True

        # State management: "DISPLAY_1" (Overworld) or "DISPLAY_2" (Machine Minigame)
        self.current_state = "DISPLAY_1"
        self.active_display = None

        # Fonts for UI
        self.font = pygame.font.Font(None, 72)
        self.sub_font = pygame.font.Font(None, 40)

        # Proximity interaction state
        self.near_machine = False
        self.active_machine = None

        # Sprite groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.machine_sprites = pygame.sprite.Group()

        # Present a deliberate loading frame before the synchronous TMX import.
        self.screen.fill((12, 25, 40))
        title = self.font.render("ARCADE ODYSSEY", True, (205, 240, 225))
        subtitle = self.sub_font.render("Preparing your adventure...", True, (115, 175, 180))
        self.screen.blit(title, title.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 35)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 35)))
        pygame.display.flip()
        pygame.event.pump()

        # Load assets and setup map
        self.load_asssets()
        self.setup()
        self.setup_background()
        self.atmosphere = Atmosphere(self.screen.get_size())
        self.camera_position = None

    def load_asssets(self):
        raw_frames = {
            'idle': import_folder(CURRENT_DIR / join("resources", "player", "BlueWizard", "idle")),
            'walk': import_folder(CURRENT_DIR / join("resources", "player", "BlueWizard", "walk")),
            'jump': import_folder(CURRENT_DIR / join("resources", "player", "BlueWizard", "jump")),
        }
        target_w = int(512 * PLAYER_SCALE)
        target_h = int(512 * PLAYER_SCALE)
        self.player_frames = {
            state: [pygame.transform.scale(img, (target_w, target_h)) for img in frames]
            for state, frames in raw_frames.items()
        }

    def setup(self):
        map_path = CURRENT_DIR / join("resources", "maps", "Map", "Overworld_map.tmx")
        tmx_map = load_pygame(map_path)

        # Bottom to top: reverse the layer list shown in Tiled.
        layer_names = (
            'Ground_background_background',
            'Collisions',
            'Ground_background',
            'Ground_background_tiles',
            'Background',
            'Arcade Machines',
            'Entity',
            'Ground',
            'Ground_foreground',
            'Hide_foreground',
        )
        scaled_images = {}

        def scale_image(image):
            if image not in scaled_images:
                size = (
                    max(1, round(image.get_width() * TILE_SCALE)),
                    max(1, round(image.get_height() * TILE_SCALE)),
                )
                scaled_images[image] = pygame.transform.scale(image, size)
            return scaled_images[image]

        for draw_layer, name in enumerate(layer_names):
            layer = tmx_map.get_layer_by_name(name)
            # Tiled visibility controls artwork, not physical boundaries.
            if not layer.visible and name != 'Collisions':
                continue

            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, image in layer.tiles():
                    pos = (x * tmx_map.tilewidth * TILE_SCALE,
                           y * tmx_map.tileheight * TILE_SCALE)
                    sprite = Sprite(pos, scale_image(image), self.all_sprites)
                    if name == 'Ground_background_tiles':
                        sprite.parallax_factor = 0.7
                    self.all_sprites.change_layer(sprite, draw_layer)

            elif isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    if not obj.visible and name != 'Collisions':
                        continue
                    pos = (obj.x * TILE_SCALE, obj.y * TILE_SCALE)
                    if name == 'Collisions':
                        size = (max(1, round(obj.width * TILE_SCALE)),
                                max(1, round(obj.height * TILE_SCALE)))
                        CollisionSprites(pos, size, self.collision_sprites)
                    elif name == 'Entity':
                        if obj.name == 'Player':
                            self.player = Player(
                                pos, self.all_sprites, self.collision_sprites,
                                self.player_frames,
                            )
                            self.player_spawn = pos
                            self.all_sprites.change_layer(self.player, draw_layer)
                    elif name == 'Arcade Machines' and obj.image:
                        # Cabinet objects can be resized in Tiled independently
                        # of their source artwork. pytmx already adjusts their
                        # bottom anchor to a top-left position.
                        size = (max(1, round(obj.width * TILE_SCALE)),
                                max(1, round(obj.height * TILE_SCALE)))
                        image = pygame.transform.scale(obj.image, size)
                        machine = Sprite(pos, image,
                                         (self.all_sprites, self.machine_sprites))
                        machine.name = str(obj.properties.get('game', obj.name)).strip()
                        self.all_sprites.change_layer(machine, draw_layer)
                    elif obj.image:
                        sprite = Sprite(pos, scale_image(obj.image), self.all_sprites)
                        self.all_sprites.change_layer(sprite, draw_layer)

    def setup_background(self):
        # Palette stops run from the leftmost scenery to the rightmost scenery.
        # Each stop stores its position (0..1), sky color, and horizon color.
        self.background_palettes = (
            (0.00, (18, 40, 75), (95, 170, 190)),    # Blue dawn
            (0.25, (14, 62, 68), (115, 185, 145)),   # Mossy forest
            (0.50, (48, 35, 85), (165, 130, 185)),   # Violet hills
            (0.75, (90, 43, 68), (240, 166, 115)),   # Sunset
            (1.00, (10, 18, 48), (65, 100, 155)),    # Night
        )
        scenery = [sprite.rect for sprite in self.all_sprites
                   if sprite is not getattr(self, 'player', None)]
        self.background_left = min((rect.left for rect in scenery), default=0)
        right = max((rect.right for rect in scenery), default=WIDTH)
        self.background_width = max(1, right - self.background_left)
        self.background_surface = None
        self.background_colors = None

    def draw_background(self, world_x):
        """Blend neighboring area palettes as the player crosses the overworld."""
        progress = max(0.0, min(1.0,
            (world_x - self.background_left) / self.background_width))
        for start, end in zip(self.background_palettes, self.background_palettes[1:]):
            if progress <= end[0]:
                blend = (progress - start[0]) / (end[0] - start[0])
                blend = blend * blend * (3 - 2 * blend)
                sky = pygame.Color(*start[1]).lerp(pygame.Color(*end[1]), blend)
                horizon = pygame.Color(*start[2]).lerp(pygame.Color(*end[2]), blend)
                break

        colors = (tuple(sky), tuple(horizon))
        if colors != self.background_colors:
            # Build a narrow strip and stretch it; reuse it until colors change.
            strip = pygame.Surface((1, HEIGHT))
            for y in range(HEIGHT):
                strip.set_at((0, y), sky.lerp(horizon, y / max(1, HEIGHT - 1)))
            self.background_surface = pygame.transform.scale(strip, (WIDTH, HEIGHT))
            self.background_colors = colors
        self.screen.blit(self.background_surface, (0, 0))

    def transition_to_machine(self):
        """Briefly zoom toward the selected cabinet and fade into its game."""
        snapshot = self.screen.copy()
        veil = pygame.Surface(self.screen.get_size())
        veil.fill('black')
        focus = pygame.Vector2(self.active_machine.rect.center) - self.all_sprites.offset
        transition_clock = pygame.time.Clock()
        elapsed = 0.0
        while elapsed < 0.3 and self.Running:
            elapsed += transition_clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.Running = False
            progress = min(1.0, elapsed / 0.3)
            scale = 1 + 0.18 * progress * progress
            enlarged = pygame.transform.scale(snapshot, (round(WIDTH * scale), round(HEIGHT * scale)))
            self.screen.blit(enlarged, (-focus.x * (scale - 1), -focus.y * (scale - 1)))
            veil.set_alpha(round(255 * progress))
            self.screen.blit(veil, (0, 0))
            pygame.display.flip()

    def check_machine_proximity(self):
        """Check if player is close enough to any arcade machine to interact."""
        self.near_machine = False
        self.active_machine = None
        closest_dist = float('inf')
        interaction_radius = max(200, int(400 * TILE_SCALE))

        if hasattr(self, 'player') and self.player.alive():
            for machine in self.machine_sprites:
                dist = math.hypot(
                    self.player.rect.centerx - machine.rect.centerx,
                    self.player.rect.centery - machine.rect.centery
                )
                if dist < interaction_radius and dist < closest_dist:
                    closest_dist = dist
                    self.near_machine = True
                    self.active_machine = machine



    def run(self):
        while self.Running:
            dt = self.clock.tick(FRAMERATE) / 1000

            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.Running = False

                # State: Overworld (Display 1)
                if self.current_state == "DISPLAY_1":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.Running = False  # Exit fullscreen game cleanly
                        elif (event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER) and self.near_machine:
                            game_name = getattr(self.active_machine, 'name', 'Arcade')
                            self.transition_to_machine()
                            if not self.Running:
                                break
                            self.active_display = get_display(game_name)
                            self.current_state = "DISPLAY_2"

                # State: Minigame (Display 2)
                elif self.current_state == "DISPLAY_2":
                    if self.active_display:
                        self.active_display.handle_event(event)
                        # Check if display requested to exit
                        if getattr(self.active_display, 'should_exit', False):
                            self.current_state = "DISPLAY_1"
                            self.active_display = None
                            self.atmosphere.reveal = 0.0

            # 2. Update & Render
            if self.current_state == "DISPLAY_1":
                # --- DISPLAY 1: OVERWORLD (Full 1920x1080) ---
                dt = min(dt, 0.05)
                self.all_sprites.update(dt)
                self.atmosphere.update(dt, getattr(self, 'player', None))
                self.check_machine_proximity()

                # Safety: if player falls into a pit in the overworld, respawn at starting platform
                if hasattr(self, 'player') and hasattr(self, 'player_spawn'):
                    if self.player.rect.top > self.player_spawn[1] + 3500:
                        self.player.rect.topleft = self.player_spawn
                        self.player.direction.y = 0
                        self.player.air_jump_available = True

                player = getattr(self, 'player', None)
                world_x = player.rect.centerx if player else self.background_left
                self.draw_background(world_x)
                target = pygame.Vector2(player.rect.center if player else (WIDTH / 2, HEIGHT / 2))
                if self.camera_position is None or self.camera_position.distance_to(target) > 1800:
                    self.camera_position = target.copy()
                else:
                    # Exponential smoothing keeps camera motion consistent across frame rates.
                    self.camera_position += (target - self.camera_position) * (1 - math.exp(-6 * dt))
                offset = self.camera_position - pygame.Vector2(WIDTH / 2, HEIGHT / 2)
                self.atmosphere.draw_back(self.screen, offset)
                self.all_sprites.draw(self.camera_position)
                self.atmosphere.draw_front(self.screen, offset, self.machine_sprites, self.active_machine)
            

            elif self.current_state == "DISPLAY_2":
                # --- DISPLAY 2: MINIGAME (Overworld is completely stopped to optimize resources) ---
                if self.active_display:
                    if hasattr(self.active_display, 'run'):
                        self.active_display.run(self.screen)
                        self.current_state = "DISPLAY_1"
                        self.active_display = None
                        self.atmosphere.reveal = 0.0
                        self.clock.tick(FRAMERATE)  # Clean timer reset upon return
                    else:
                        self.active_display.update(dt)
                        self.active_display.draw(self.screen)

            pygame.display.update()

        pygame.quit()


if __name__ == "__main__":
    Game().run()
