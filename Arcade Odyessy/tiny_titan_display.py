import os
import sys
import math
import random
from array import array
from pathlib import Path
import pygame
from settigns import WIDTH, HEIGHT, CURRENT_DIR

# =========================================================================
# TINY TITAN (Native 800x700 resolution)
# =========================================================================
TITAN_BASE = str((CURRENT_DIR.parent / "Tiny titan").resolve())
TITAN_ASSETS = os.path.join(TITAN_BASE, "assets")

TITAN_WIDTH = 800
TITAN_HEIGHT = 700
TITAN_FPS = 60
TITAN_PLAYER_VEL = 5
TITAN_BLOCK_SIZE = 96
TITAN_FLOOR_Y = TITAN_HEIGHT - TITAN_BLOCK_SIZE
TITAN_START_LIVES = 2

TITAN_LEVELS = [
    {
        "background": "Blue.png",
        "length": 30,
        "holes": [(10, 2)],
        "blocks": [(16, 1), (17, 1), (18, 2), (19, 2)],
        "fruits": [(3, 1), (5, 1), (8, 1), (10, 2), (11, 2), (16, 2), (17, 2),
                   (18, 3), (19, 3), (22, 2), (24, 1), (26, 1)],
        "rhinos": [(3, 3, 4), (6, 6, 7), (24, 23, 25)],
        "bats": [],
        "fires": [22],
        "spikes": [],
        "flag": 27,
    },
    {
        "background": "Green.png",
        "length": 40,
        "holes": [(9, 2), (23, 2)],
        "blocks": [(14, 1), (15, 1), (16, 2), (17, 2), (29, 1), (30, 1), (31, 2), (32, 2)],
        "fruits": [(3, 1), (5, 2), (7, 1), (9, 2), (10, 2), (12, 1), (14, 2), (15, 2),
                   (16, 3), (17, 3), (20, 1), (23, 2), (24, 2), (26, 1), (29, 2),
                   (30, 2), (31, 3), (32, 3), (34, 2), (35, 1)],
        "rhinos": [(19, 18, 20), (6, 6, 7)],
        "bats": [(12, 3, 11, 15)],
        "fires": [27, 34],
        "spikes": [5],
        "flag": 37,
    },
]

TITAN_BEEPS = {
    "jump": (500, 0.12),
    "fruit": (1100, 0.10),
    "stomp": (200, 0.15),
    "hurt": (130, 0.35),
    "win": (800, 0.40),
    "lose": (100, 0.60),
}


def make_titan_beep(pitch, seconds):
    rate = 44100
    count = int(rate * seconds)
    samples = array("h")
    for i in range(count):
        wave = math.sin(2 * math.pi * pitch * i / rate)
        fade = 1 - i / count
        samples.append(int(8000 * wave * fade))
    try:
        return pygame.mixer.Sound(buffer=samples.tobytes())
    except Exception:
        return None


def load_titan_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = os.path.join(TITAN_ASSETS, dir1, dir2)
    if not os.path.exists(path):
        return {}
    images = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    all_sprites = {}
    for image in images:
        sprite_sheet = pygame.image.load(os.path.join(path, image)).convert_alpha()
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = [
                pygame.transform.flip(s, True, False) for s in sprites
            ]
        else:
            all_sprites[image.replace(".png", "")] = sprites
    return all_sprites


def get_titan_block(size):
    path = os.path.join(TITAN_ASSETS, "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class TitanPlayer(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height, sprites):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "right"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.sprites = sprites
        self.update_sprite()

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def bounce(self):
        self.y_vel = -self.GRAVITY * 8
        self.fall_count = 0
        self.jump_count = 1

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.sprites.get(sprite_sheet_name, self.sprites.get("idle_right", []))
        if sprites:
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.sprite = sprites[sprite_index]
            self.animation_count += 1
            self.update()

    def update(self):
        if hasattr(self, 'sprite'):
            self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
            self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        if hasattr(self, 'sprite'):
            win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class TitanObject(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.mask = pygame.mask.from_surface(self.image)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

    def loop(self):
        pass


class TitanBlock(TitanObject):
    def __init__(self, x, y, size, block_image):
        super().__init__(x, y, size, size)
        self.image.blit(block_image, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class TitanFire(TitanObject):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height, sprites):
        super().__init__(x, y, width, height, "fire")
        self.fire = sprites
        self.image = self.fire["on"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0

    def loop(self):
        sprites = self.fire["on"]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)


class TitanSpikes(TitanObject):
    def __init__(self, x, y, spike_sprite):
        super().__init__(x, y, TITAN_BLOCK_SIZE, 32, "spikes")
        for i in range(3):
            self.image.blit(spike_sprite, (i * 32, 0))
        self.mask = pygame.mask.from_surface(self.image)


class TitanFruit(TitanObject):
    ANIMATION_DELAY = 2
    KINDS = ["Apple", "Orange", "Bananas", "Cherries", "Strawberry", "Kiwi", "Melon", "Pineapple"]

    def __init__(self, x, y, kind, sprites):
        super().__init__(x, y, 64, 64, "fruit")
        self.kind = kind
        self.sprites = sprites
        self.animation_count = 0

    def loop(self):
        sprites = self.sprites.get(self.kind, [])
        if sprites:
            self.image = sprites[(self.animation_count // self.ANIMATION_DELAY) % len(sprites)]
            self.animation_count += 1


class TitanEnemy(TitanObject):
    ANIMATION_DELAY = 3
    SPEED = 2
    SHEET = {"rhino": "Run (52x34)", "bat": "Flying (46x30)"}

    def __init__(self, kind, x, y, left, right, sprites):
        self.enemy_sprites = sprites
        width, height = self.enemy_sprites[kind][self.SHEET[kind] + "_left"][0].get_size()
        super().__init__(x, y, width, height, kind)
        self.start_y = y
        self.left = left
        self.right = right
        self.vel = -self.SPEED
        self.wave = 0
        self.animation_count = 0

    def loop(self):
        self.rect.x += self.vel
        if self.rect.x <= self.left or self.rect.x >= self.right:
            self.vel *= -1

        if self.name == "bat":
            self.wave += 0.05
            self.rect.y = self.start_y + int(math.sin(self.wave) * 30)

        facing = "right" if self.vel < 0 else "left"
        sprites = self.enemy_sprites[self.name][self.SHEET[self.name] + "_" + facing]
        self.image = sprites[(self.animation_count // self.ANIMATION_DELAY) % len(sprites)]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count += 1


class TitanFlag(TitanObject):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, sprites):
        super().__init__(x, y, 128, 128, "flag")
        self.flag_sprites = sprites
        self.image = self.flag_sprites["Checkpoint (Flag Idle)(64x64)"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0

    def loop(self):
        sprites = self.flag_sprites["Checkpoint (Flag Idle)(64x64)"]
        self.image = sprites[(self.animation_count // self.ANIMATION_DELAY) % len(sprites)]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)


class TitanLevel:
    def __init__(self, number, assets):
        data = TITAN_LEVELS[number]
        self.length = data["length"] * TITAN_BLOCK_SIZE
        self.background_name = data["background"]

        hole_columns = set()
        for start, width in data["holes"]:
            for column in range(start, start + width):
                hole_columns.add(column)

        self.blocks = [
            TitanBlock(c * TITAN_BLOCK_SIZE, TITAN_FLOOR_Y, TITAN_BLOCK_SIZE, assets["block"])
            for c in range(data["length"]) if c not in hole_columns
        ]

        for column, height in data["blocks"]:
            self.blocks.append(
                TitanBlock(column * TITAN_BLOCK_SIZE, TITAN_FLOOR_Y - height * TITAN_BLOCK_SIZE, TITAN_BLOCK_SIZE, assets["block"])
            )

        self.fruits = []
        for column, height in data["fruits"]:
            kind = TitanFruit.KINDS[(column + height) % len(TitanFruit.KINDS)]
            self.fruits.append(
                TitanFruit(column * TITAN_BLOCK_SIZE + 16, TITAN_FLOOR_Y - height * TITAN_BLOCK_SIZE + 16, kind, assets["fruits"])
            )

        self.enemies = []
        for column, left, right in data["rhinos"]:
            self.enemies.append(
                TitanEnemy("rhino", column * TITAN_BLOCK_SIZE + 12, TITAN_FLOOR_Y - 68,
                           left * TITAN_BLOCK_SIZE, right * TITAN_BLOCK_SIZE, assets["enemies"])
            )
        for column, height, left, right in data["bats"]:
            self.enemies.append(
                TitanEnemy("bat", column * TITAN_BLOCK_SIZE, TITAN_FLOOR_Y - height * TITAN_BLOCK_SIZE + 18,
                           left * TITAN_BLOCK_SIZE, right * TITAN_BLOCK_SIZE, assets["enemies"])
            )

        self.traps = [
            TitanFire(c * TITAN_BLOCK_SIZE + 32, TITAN_FLOOR_Y - 64, 32, 64, assets["fire"])
            for c in data["fires"]
        ]
        self.traps += [
            TitanSpikes(c * TITAN_BLOCK_SIZE, TITAN_FLOOR_Y - 32, assets["spikes"])
            for c in data["spikes"]
        ]

        self.flag = TitanFlag(data["flag"] * TITAN_BLOCK_SIZE - 16, TITAN_FLOOR_Y - 128, assets["flag"])
        self.start = (TITAN_BLOCK_SIZE + 16, TITAN_FLOOR_Y - 70)
        self.total_fruits = len(self.fruits)


def titan_handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
            collided_objects.append(obj)
    return collided_objects


def titan_collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    player.move(-dx, 0)
    player.update()
    return collided_object


def titan_handle_move(player, objects):
    keys = pygame.key.get_pressed()
    player.x_vel = 0

    collide_left = titan_collide(player, objects, -TITAN_PLAYER_VEL * 2)
    collide_right = titan_collide(player, objects, TITAN_PLAYER_VEL * 2)

    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collide_left:
        player.move_left(TITAN_PLAYER_VEL)
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collide_right:
        player.move_right(TITAN_PLAYER_VEL)

    titan_handle_vertical_collision(player, objects, player.y_vel)


def titan_hurt(player, lives, sounds):
    if player.hit:
        return lives
    player.make_hit()
    player.y_vel = -6
    player.fall_count = 0
    if sounds and sounds.get("hurt"):
        sounds["hurt"].play()
    return lives


def draw_titan_heart(surface, x, y, size, color):
    r = size // 4
    pygame.draw.circle(surface, color, (x + r, y + r), r)
    pygame.draw.circle(surface, color, (x + size - r, y + r), r)
    pygame.draw.polygon(surface, color, [(x, y + r), (x + size, y + r), (x + size // 2, y + size)])


def draw_titan_text(surface, text, size, center=None, topleft=None, color=(255, 255, 255)):
    font = pygame.font.Font(None, size)
    shadow = font.render(text, True, (0, 0, 0))
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = center
    if topleft:
        rect.topleft = topleft
    surface.blit(shadow, rect.move(2, 2))
    surface.blit(image, rect)


class TinyTitanDisplay:
    """
    Tiny Titan Game Display (Native 800x700 resolution)
    - Full native game logic, assets, physics, animations, and sound effects
    - Runs inside its exact 800x700 canvas, centered within the 1920x1080 overworld
    - Overworld is completely stopped while playing
    - ESC returns smoothly to the overworld without crashing
    """
    def __init__(self, game_name="Tiny titan"):
        self.game_name = game_name
        self.orig_width = TITAN_WIDTH   # 800
        self.orig_height = TITAN_HEIGHT # 700
        self.game_surface = pygame.Surface((self.orig_width, self.orig_height))
        self.assets = None
        self.sounds = None

    def _init_assets(self):
        if self.assets is not None:
            return

        self.assets = {
            "player": load_titan_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True),
            "block": get_titan_block(TITAN_BLOCK_SIZE),
            "fire": load_titan_sprite_sheets("Traps", "Fire", 16, 32),
            "spikes": pygame.transform.scale2x(
                pygame.image.load(os.path.join(TITAN_ASSETS, "Traps", "Spikes", "Idle.png")).convert_alpha()
            ),
            "fruits": load_titan_sprite_sheets("Items", "Fruits", 32, 32),
            "enemies": {
                "rhino": load_titan_sprite_sheets("Enemies", "Rino", 52, 34, True),
                "bat": load_titan_sprite_sheets("Enemies", "Bat", 46, 30, True),
            },
            "flag": load_titan_sprite_sheets("Items", os.path.join("Checkpoints", "Checkpoint"), 64, 64),
            "backgrounds": {},
        }

        # Cache background images
        for bg_file in ("Blue.png", "Green.png", "Brown.png", "Gray.png", "Pink.png", "Purple.png", "Yellow.png"):
            bg_path = os.path.join(TITAN_ASSETS, "Background", bg_file)
            if os.path.exists(bg_path):
                self.assets["backgrounds"][bg_file] = pygame.image.load(bg_path).convert()

        # Initialize synthesized sound effects
        self.sounds = {}
        for name, (pitch, sec) in TITAN_BEEPS.items():
            snd = make_titan_beep(pitch, sec)
            if snd:
                self.sounds[name] = snd

    def _get_background_tiles(self, bg_image):
        _, _, width, height = bg_image.get_rect()
        tiles = []
        for i in range(self.orig_width // width + 1):
            for j in range(self.orig_height // height + 1):
                tiles.append((i * width, j * height))
        return tiles

    def run(self, screen):
        self._init_assets()

        clock = pygame.time.Clock()
        hud_font = pygame.font.Font(None, 36)

        score = 0
        lives = TITAN_START_LIVES
        level_number = 0

        running = True
        while running:
            # Load level
            level = TitanLevel(level_number, self.assets)
            bg_img = self.assets["backgrounds"].get(
                level.background_name,
                next(iter(self.assets["backgrounds"].values()))
            )
            bg_tiles = self._get_background_tiles(bg_img)
            player = TitanPlayer(*level.start, 50, 50, self.assets["player"])

            offset_x = 0
            scroll_area_width = 200
            level_state = "playing"  # "playing", "won", "dead"

            while level_state == "playing":
                clock.tick(TITAN_FPS)

                # Event handling
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            return
                        if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP) and player.jump_count < 2:
                            player.jump()
                            if self.sounds.get("jump"):
                                self.sounds["jump"].play()

                # Updates
                player.loop(TITAN_FPS)
                for obj in level.traps + level.fruits + level.enemies + [level.flag]:
                    obj.loop()

                titan_handle_move(player, level.blocks)

                if player.rect.left < 0:
                    player.rect.left = 0
                if player.rect.right > level.length:
                    player.rect.right = level.length

                # Trap collisions
                for trap in level.traps:
                    if pygame.sprite.collide_mask(player, trap):
                        lives = titan_hurt(player, lives, self.sounds)

                # Enemy collisions
                for enemy in level.enemies[:]:
                    if pygame.sprite.collide_mask(player, enemy):
                        from_above = player.y_vel > 0 and player.rect.bottom <= enemy.rect.centery + 12
                        if from_above:
                            level.enemies.remove(enemy)
                            player.bounce()
                            score += 100
                            if self.sounds.get("stomp"):
                                self.sounds["stomp"].play()
                        else:
                            lives = titan_hurt(player, lives, self.sounds)

                # Fruit collection
                for fruit in level.fruits[:]:
                    if player.rect.colliderect(fruit.rect.inflate(-16, -16)):
                        level.fruits.remove(fruit)
                        score += 10
                        if self.sounds.get("fruit"):
                            self.sounds["fruit"].play()

                # Fall off bottom of screen
                if player.rect.top > self.orig_height:
                    lives -= 1
                    if self.sounds.get("hurt"):
                        self.sounds["hurt"].play()
                    if lives > 0:
                        player = TitanPlayer(*level.start, 50, 50, self.assets["player"])
                        player.make_hit()
                        offset_x = 0

                # Check game over
                if lives <= 0:
                    level_state = "dead"
                    break

                # Check flag reached
                if pygame.sprite.collide_mask(player, level.flag):
                    level_state = "won"
                    score += 100
                    break

                # Camera scrolling
                if ((player.rect.right - offset_x >= self.orig_width - scroll_area_width) and player.x_vel > 0) or (
                        (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                    offset_x += player.x_vel
                offset_x = max(0, min(offset_x, level.length - self.orig_width))

                # Render to 800x700 game surface
                for tile in bg_tiles:
                    self.game_surface.blit(bg_img, tile)

                for group in (level.blocks, level.traps, level.fruits, level.enemies):
                    for obj in group:
                        if obj.rect.right - offset_x > 0 and obj.rect.left - offset_x < self.orig_width:
                            obj.draw(self.game_surface, offset_x)

                level.flag.draw(self.game_surface, offset_x)
                player.draw(self.game_surface, offset_x)

                # Top HUD Bar
                hud_bar = pygame.Surface((self.orig_width, 60), pygame.SRCALPHA)
                hud_bar.fill((0, 0, 0, 140))
                self.game_surface.blit(hud_bar, (0, 0))

                for i in range(TITAN_START_LIVES):
                    color = (255, 60, 100) if i < lives else (90, 70, 80)
                    draw_titan_heart(self.game_surface, 14 + i * 42, 14, 34, color)

                apple_img = self.assets["fruits"].get("Apple", [None])[0]
                if apple_img:
                    self.game_surface.blit(pygame.transform.scale(apple_img, (48, 48)), (160, 6))
                collected = level.total_fruits - len(level.fruits)
                draw_titan_text(self.game_surface, f"{collected}/{level.total_fruits}", 36, topleft=(214, 18))
                draw_titan_text(self.game_surface, f"Score: {score}", 40, center=(self.orig_width // 2, 30))
                draw_titan_text(self.game_surface, f"Level {level_number + 1}", 36, topleft=(self.orig_width - 150, 18))

                # Center on 1920x1080 screen
                screen.fill((0, 0, 0))
                pos_x = (WIDTH - self.orig_width) // 2
                pos_y = (HEIGHT - self.orig_height) // 2
                screen.blit(self.game_surface, (pos_x, pos_y))

                frame_rect = pygame.Rect(pos_x - 4, pos_y - 4, self.orig_width + 8, self.orig_height + 8)
                pygame.draw.rect(screen, (255, 200, 50), frame_rect, width=3, border_radius=6)

                hint = hud_font.render(
                    "TINY TITAN  |  A/D or Arrows: Move  |  Space/W: Jump (Double Jump)  |  ESC: Exit",
                    True,
                    (180, 180, 200)
                )
                screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

                pygame.display.update()

            # Handle Level Transitions:
            if level_state == "won":
                if self.sounds.get("win"):
                    self.sounds["win"].play()
                level_number += 1
                if level_number >= len(TITAN_LEVELS):
                    # Show Win Screen
                    if not self._show_message(screen, "YOU WIN!", score, hud_font):
                        return
                    score, lives, level_number = 0, TITAN_START_LIVES, 0

            elif level_state == "dead":
                if self.sounds.get("lose"):
                    self.sounds["lose"].play()
                if not self._show_message(screen, "GAME OVER", score, hud_font):
                    return
                score, lives, level_number = 0, TITAN_START_LIVES, 0

    def _show_message(self, screen, title, score, hud_font):
        """Displays Win/Loss banner on the 800x700 game screen, returns True to restart, False to exit."""
        self.game_surface.fill((25, 25, 45))
        draw_titan_text(self.game_surface, title, 90, center=(self.orig_width // 2, 280), color=(255, 220, 80))
        draw_titan_text(self.game_surface, f"Final Score: {score}", 48, center=(self.orig_width // 2, 380))
        draw_titan_text(self.game_surface, "Press ENTER to Play Again  |  ESC to Exit", 34, center=(self.orig_width // 2, 470), color=(180, 220, 255))

        pos_x = (WIDTH - self.orig_width) // 2
        pos_y = (HEIGHT - self.orig_height) // 2

        screen.fill((0, 0, 0))
        screen.blit(self.game_surface, (pos_x, pos_y))
        frame_rect = pygame.Rect(pos_x - 4, pos_y - 4, self.orig_width + 8, self.orig_height + 8)
        pygame.draw.rect(screen, (255, 200, 50), frame_rect, width=3, border_radius=6)

        hint = hud_font.render("ENTER: Restart  |  ESC: Return to Overworld", True, (180, 180, 200))
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 40)))
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
            pygame.time.Clock().tick(60)  # Prevent CPU spin during wait screen
        return False

