from settigns import *
from All_sprite import AllSprites
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

        # Load assets and setup map
        self.load_asssets()
        self.setup()

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
        tmx_map = load_pygame(CURRENT_DIR / join("resources", "maps", "Mossy Tileset", "map1.tmx"))

        # 1. Collision objects from map (scaled by TILE_SCALE)
        try:
            for obj in tmx_map.get_layer_by_name("Colisions"):
                c_pos = (obj.x * TILE_SCALE, obj.y * TILE_SCALE)
                c_size = (obj.width * TILE_SCALE, obj.height * TILE_SCALE)
                CollisionSprites(c_pos, c_size, self.collision_sprites)
        except Exception:
            pass


        # 3. Machines layer (supports Object Layer & Tile Layer, scaled by TILE_SCALE)
        try:
            machine_layer = tmx_map.get_layer_by_name("Machines")
            # If it is an Object Group
            if hasattr(machine_layer, '__iter__') and not hasattr(machine_layer, 'tiles'):
                for obj in machine_layer:
                    m_w = int(getattr(obj, 'width', 256) * TILE_SCALE)
                    m_h = int(getattr(obj, 'height', 256) * TILE_SCALE)

                    image = getattr(obj, 'image', None)
                    if image is not None:
                        # Scale image and remove black background
                        image = pygame.transform.scale(image, (m_w, m_h)).convert_alpha()
                        image.set_colorkey((0, 0, 0))
                    else:
                        image = pygame.Surface((m_w, m_h), pygame.SRCALPHA)
                        image.fill((0, 200, 255, 200))

                    # Position machine so its bottom aligns with the ground
                    pos_y = obj.y * TILE_SCALE - m_h if getattr(obj, 'gid', 0) else obj.y * TILE_SCALE
                    pos = (obj.x * TILE_SCALE, pos_y)

                    machine = Sprite(pos, image, (self.all_sprites, self.machine_sprites))
                    machine.name = obj.name.strip() if obj.name else "Arcade"

            # If it is a Tile Layer
            elif hasattr(machine_layer, 'tiles'):
                m_offset_x = getattr(machine_layer, 'offsetx', 0)
                m_offset_y = getattr(machine_layer, 'offsety', 0)
                for x, y, image in machine_layer.tiles():
                    pos = (x * TILE_SIZE + int(m_offset_x * TILE_SCALE), y * TILE_SIZE + int(m_offset_y * TILE_SCALE))
                    scaled_image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
                    machine = Sprite(pos, scaled_image, (self.all_sprites, self.machine_sprites))
                    machine.name = "Arcade"

        except Exception as e:
            print("Notice: could not load Machines layer:", e)

        # 4. Entities (Player spawn scaled by TILE_SCALE)
        for obj in tmx_map.get_layer_by_name("Entities"):
            if obj.name and obj.name.strip().lower() == "player":
                player_pos = (obj.x * TILE_SCALE, obj.y * TILE_SCALE)
                self.player = Player(player_pos, self.all_sprites, self.collision_sprites, self.player_frames)
        # 2. Ground tiles (scaled by TILE_SCALE)
        ground_layer = tmx_map.get_layer_by_name("Ground")
        offset_x = getattr(ground_layer, 'offsetx', 0)
        offset_y = getattr(ground_layer, 'offsety', 0)
        collide_tiles = len(self.collision_sprites) == 0

        for x, y, image in ground_layer.tiles():
            pos = (x * TILE_SIZE + int(offset_x * TILE_SCALE), y * TILE_SIZE + int(offset_y * TILE_SCALE))
            scaled_image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
            groups = (self.all_sprites, self.collision_sprites) if collide_tiles else self.all_sprites
            Sprite(pos, scaled_image, groups)

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

    # Human-readable names for each arcade machine
    MACHINE_NAMES = {
        "tiny titan":               "Tiny Titan",
        "flappy-bird-game-main":    "Flappy Bird",
        "pong":                     "Pong",
        "vampire survivor":         "Vampire Survivor",
        "space shooter":            "Space Shooter",
        "pixel-runner-game-main":   "Pixel Runner",
        "ninja game":               "Ninja Game",
        "arcade":                   "Arcade",
    }

    def draw_ui(self):
        """Draw 'Enter to Play' prompt when player is near a machine."""
        if self.near_machine:
            raw_name = getattr(self.active_machine, 'name', '').strip()
            machine_title = self.MACHINE_NAMES.get(raw_name.lower(), raw_name.title())
            prompt_text = f"Enter to Play: {machine_title}" if machine_title else "Enter to Play"
            text_surf = self.font.render(prompt_text, True, (255, 255, 255))

            # UI box dimensions
            padding_x, padding_y = 40, 20
            w = text_surf.get_width() + padding_x * 2
            h = text_surf.get_height() + padding_y * 2

            # Position at bottom-center of the screen
            box_rect = pygame.Rect((WIDTH - w) // 2, HEIGHT - 180, w, h)

            # Draw semi-transparent arcade badge with neon border
            bg_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, (15, 15, 25, 220), bg_surf.get_rect(), border_radius=16)
            pygame.draw.rect(bg_surf, (0, 255, 200, 255), bg_surf.get_rect(), width=4, border_radius=16)

            self.screen.blit(bg_surf, box_rect.topleft)
            self.screen.blit(text_surf, text_surf.get_rect(center=box_rect.center))

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
                            self.active_display = get_display(game_name)
                            self.current_state = "DISPLAY_2"

                # State: Minigame (Display 2)
                elif self.current_state == "DISPLAY_2":
                    if self.active_display:
                        self.active_display.handle_event(event)
                        # Check if display requested to exit
                        if self.active_display.should_exit:
                            self.current_state = "DISPLAY_1"
                            self.active_display = None

            # 2. Update & Render
            if self.current_state == "DISPLAY_1":
                # --- DISPLAY 1: OVERWORLD (Full 1920x1080) ---
                self.all_sprites.update(dt)
                self.check_machine_proximity()

                self.screen.fill((10, 10, 20))
                if hasattr(self, 'player') and self.player.alive():
                    self.all_sprites.draw(self.player.rect.center)
                else:
                    self.all_sprites.draw((WIDTH / 2, HEIGHT / 2))

                # Draw UI prompt on top of overworld
                self.draw_ui()

            elif self.current_state == "DISPLAY_2":
                # --- DISPLAY 2: MINIGAME (Overworld is completely stopped to optimize resources) ---
                if self.active_display:
                    if hasattr(self.active_display, 'run'):
                        self.active_display.run(self.screen)
                        self.current_state = "DISPLAY_1"
                        self.active_display = None
                        self.clock.tick(FRAMERATE)  # Clean timer reset upon return
                    else:
                        self.active_display.update(dt)
                        self.active_display.draw(self.screen)

            pygame.display.update()

        pygame.quit()


if __name__ == "__main__":
    Game().run()
