from settigns import *
from All_sprite import AllSprites
from startup import StartupScreen
from ambient_audio import AmbientMusic
from machine_audio import MachineAudio
from atmosphere import Atmosphere
from arcade_screen import begin_game_transition, clear_game_transition, ArcadeScreen, NinjaArcadeScreen
from plants import add_ground_plants
from slimes import add_slimes
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

        self.startup = StartupScreen(self.screen)
        self.startup.draw(0.05, 'Awakening the forest...')

        self.load_asssets()
        self.startup.draw(0.20, "Preparing the overworld...")
        self.setup()
        self.startup.draw(0.92, "Lighting up the arcades...")
        self.setup_background()
        self.atmosphere = Atmosphere(
            self.screen.get_size(), self.machine_sprites, self.collision_sprites
        )
        self.camera_position = None
        self.machine_audio = MachineAudio()
        self.ambient_music = AmbientMusic()
        self.startup.draw(1.0, "Your adventure is ready.")

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

        self.plants = add_ground_plants(
            tmx_map, self.all_sprites, self.machine_sprites,
            getattr(self, 'player', None),
            CURRENT_DIR / 'resources' / 'Plant Animations',
            TILE_SCALE, layer_names.index('Ground'),
        )

        self.slimes = add_slimes(
            tmx_map, self.all_sprites, self.machine_sprites,
            getattr(self, 'player', None), self.plants,
            CURRENT_DIR / 'resources' / 'Slimes',
            TILE_SCALE, layer_names.index('Ground'),
        )

    def setup_background(self):
        # Palette stops run from the leftmost scenery to the rightmost scenery.
        # Each stop stores its position (0..1), sky color, and horizon color.
        self.background_palettes = (
            (0.00, (9, 17, 39), (35, 76, 90)),     # Moonlit blue
            (0.25, (8, 23, 38), (32, 83, 74)),    # Enchanted forest
            (0.50, (20, 18, 47), (63, 65, 96)),   # Violet night
            (0.75, (25, 19, 43), (77, 61, 85)),   # Muted plum horizon
            (1.00, (7, 13, 34), (29, 57, 82)),    # Deep navy
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
                strip.set_at((0, y), sky.lerp(horizon, (y / max(1, HEIGHT - 1)) ** 1.35))
            self.background_surface = pygame.transform.scale(strip, (WIDTH, HEIGHT))
            self.background_colors = colors
        self.screen.blit(self.background_surface, (0, 0))

    def machine_screen_view(self, machine):
        """Match the inner glass opening in the overworld cabinet artwork."""
        rect = machine.rect
        name = getattr(machine, 'name', '').strip().lower()
        # These two cabinets have slightly wider, lower glass openings.
        if 'platform' in name:
            opening = (0.28, 0.282, 0.40, 0.18)
        elif 'pixel' in name or 'runner' in name:
            opening = (0.282, 0.284, 0.40, 0.18)
        else:
            opening = (0.29, 0.28, 0.39, 0.175)
        x, y, width, height = opening
        glass = pygame.FRect(rect.x + rect.width * x, rect.y + rect.height * y,
                            rect.width * width, rect.height * height)
        glass_center = glass.center
        glass.move_ip(-self.all_sprites.offset.x, -self.all_sprites.offset.y)
        # Fill the window without stretching the cabinet artwork.
        presentation = NinjaArcadeScreen if 'ninja' in getattr(machine, 'name', '').lower() else ArcadeScreen
        ratio = presentation.GLASS.width / presentation.GLASS.height
        if glass.width / glass.height < ratio:
            glass.height = glass.width / ratio
        else:
            glass.width = glass.height * ratio
        glass.center = (glass_center[0] - self.all_sprites.offset.x,
                        glass_center[1] - self.all_sprites.offset.y)
        return glass

    def draw_transition_frame(self, progress, returning=False):
        full = pygame.FRect(self.hub_snapshot.get_rect())
        # Smoothstep has zero velocity at both ends.
        eased = progress * progress * (3 - 2 * progress)
        zoom = 1 - eased if returning else eased
        target = self.hub_screen_view
        view = pygame.FRect(full.x + (target.x - full.x) * zoom,
                            full.y + (target.y - full.y) * zoom,
                            full.width + (target.width - full.width) * zoom,
                            full.height + (target.height - full.height) * zoom)
        crop = pygame.Rect(round(view.x), round(view.y),
                           max(1, round(view.width)), max(1, round(view.height)))
        # A bounded crop avoids allocating enormous zoomed copies of the hub.
        frame = pygame.Surface(crop.size)
        frame.blit(self.hub_snapshot, (0, 0), crop)
        if returning and progress < 0.4:
            flash = pygame.Surface(crop.size, pygame.SRCALPHA)
            glass = pygame.Rect(round(target.x - crop.x), round(target.y - crop.y),
                                round(target.width), round(target.height))
            pygame.draw.rect(flash, (215, 255, 240, round(235 * (1 - progress / 0.4) ** 2)), glass)
            frame.blit(flash, (0, 0))
        pygame.transform.smoothscale(frame, self.screen.get_size(), self.screen)

    def animate_machine_transition(self, returning=False):
        transition_clock = pygame.time.Clock()
        elapsed = 0.0
        duration = 1.0 if returning else 0.85
        while self.Running:
            elapsed += transition_clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.Running = False
            progress = min(1.0, elapsed / duration)
            self.draw_transition_frame(progress, returning)
            pygame.display.flip()
            if progress >= 1:
                break
        self.clock.tick()  # Exclude transition time from game physics.

    def transition_to_machine(self):
        # Preserve the wizard in the hub; the live game grows over the glass.
        self.hub_snapshot = self.screen.copy()
        self.hub_screen_view = self.machine_screen_view(self.active_machine)
        self.entry_foreground = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        player = getattr(self, 'player', None)
        if player:
            position = pygame.Vector2(player.image_rect.topleft) - self.all_sprites.offset
            self.entry_foreground.blit(player.image, position)

    def return_to_hub(self):
        clear_game_transition()
        self.current_state = "DISPLAY_1"
        self.active_display = None
        self.atmosphere.reveal = 1.0
        if hasattr(self, 'hub_snapshot'):
            self.animate_machine_transition(returning=True)

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



    def fade_out_on_exit(self):
        """Ease the last visible frame and all audio to silence before closing."""
        if not pygame.display.get_init() or pygame.display.get_surface() is None:
            return
        duration = 0.6
        snapshot = self.screen.copy()
        veil = pygame.Surface(self.screen.get_size())
        veil.fill('black')
        if pygame.mixer.get_init():
            pygame.mixer.fadeout(round(duration * 1000))
            pygame.mixer.music.fadeout(round(duration * 1000))
        exit_clock = pygame.time.Clock()
        elapsed = 0.0
        while elapsed < duration:
            elapsed += exit_clock.tick(60) / 1000
            pygame.event.pump()
            # Keep the window responsive without forwarding inputs to gameplay.
            pygame.event.get()
            progress = min(1.0, elapsed / duration)
            eased = progress * progress * (3 - 2 * progress)
            self.screen.blit(snapshot, (0, 0))
            veil.set_alpha(round(255 * eased))
            self.screen.blit(veil, (0, 0))
            pygame.display.flip()

    def run(self):
        if not self.startup.show():
            self.fade_out_on_exit()
            pygame.quit()
            return
        self.clock.tick(FRAMERATE)
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
                            self.ambient_music.stop()
                            self.machine_audio.stop()
                            self.transition_to_machine()
                            if not self.Running:
                                break
                            self.active_display = get_display(game_name)
                            begin_game_transition(self.hub_snapshot, self.hub_screen_view, self.entry_foreground)
                            self.current_state = "DISPLAY_2"

                # State: Minigame (Display 2)
                elif self.current_state == "DISPLAY_2":
                    if self.active_display:
                        self.active_display.handle_event(event)
                        # Check if display requested to exit
                        if getattr(self.active_display, 'should_exit', False):
                            self.return_to_hub()

            if not self.Running:
                break

            # 2. Update & Render
            if self.current_state == "DISPLAY_1":
                # --- DISPLAY 1: OVERWORLD (Full 1920x1080) ---
                dt = min(dt, 0.05)
                self.all_sprites.update(dt)
                self.atmosphere.update(dt, getattr(self, 'player', None))
                self.check_machine_proximity()
                self.machine_audio.update(dt, getattr(self, 'player', None), self.machine_sprites)
                self.ambient_music.update(dt, max(self.machine_audio.volumes.values(), default=0.0))

                # Safety: if player falls into a pit in the overworld, respawn at starting platform
                if hasattr(self, 'player') and hasattr(self, 'player_spawn'):
                    if self.player.rect.top > self.player_spawn[1] + 3500:
                        self.player.rect.topleft = self.player_spawn
                        self.player.direction.y = 0
                        self.player.jump_count = 0

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
                        self.return_to_hub()
                    else:
                        self.active_display.update(dt)
                        self.active_display.draw(self.screen)

            pygame.display.update()

        self.fade_out_on_exit()
        self.ambient_music.stop()
        self.machine_audio.stop()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
