import math
import os
from array import array
from os import listdir
from os.path import isfile, join
 
import pygame
 
pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()
 
pygame.display.set_caption("Tiny Titan")
 
WIDTH, HEIGHT = 800, 700
FPS = 60
PLAYER_VEL = 5
BLOCK_SIZE = 96
FLOOR_Y = HEIGHT - BLOCK_SIZE
START_LIVES = 2
 
ASSETS = join(os.path.dirname(os.path.abspath(__file__)), "assets")
 
window = pygame.display.set_mode((WIDTH, HEIGHT))
 
LEVELS = [
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
 
 
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]
 
 
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join(ASSETS, dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]
 
    all_sprites = {}
 
    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
 
        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))
 
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
 
    return all_sprites
 
 
def get_block(size):
    path = join(ASSETS, "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)
 
 
BEEPS = {
    "jump": (500, 0.12),
    "fruit": (1100, 0.10),
    "stomp": (200, 0.15),
    "hurt": (130, 0.35),
    "win": (800, 0.40),
    "lose": (100, 0.60),
}
sounds = {}
 
 
def make_beep(pitch, seconds):
    rate = 44100
    count = int(rate * seconds)
    samples = array("h")
    for i in range(count):
        wave = math.sin(2 * math.pi * pitch * i / rate)
        fade = 1 - i / count
        samples.append(int(8000 * wave * fade))
    return pygame.mixer.Sound(buffer=samples.tobytes())
 
 
def load_sounds():
    try:
        for name, (pitch, seconds) in BEEPS.items():
            sounds[name] = make_beep(pitch, seconds)
    except pygame.error:
        pass
 
 
def play_sound(name):
    if name in sounds:
        sounds[name].play()
 
 
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
    ANIMATION_DELAY = 3
 
    def __init__(self, x, y, width, height):
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
        self.count = 0
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
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()
 
    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)
 
    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))
 
 
class Object(pygame.sprite.Sprite):
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
 
 
class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)
 
 
class Fire(Object):
    ANIMATION_DELAY = 3
    SPRITES = load_sprite_sheets("Traps", "Fire", 16, 32)
 
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = self.SPRITES
        self.image = self.fire["on"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
 
    def loop(self):
        sprites = self.fire["on"]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)
 
 
class Spikes(Object):
    SPRITE = pygame.transform.scale2x(
        pygame.image.load(join(ASSETS, "Traps", "Spikes", "Idle.png")).convert_alpha())
 
    def __init__(self, x, y):
        super().__init__(x, y, BLOCK_SIZE, 32, "spikes")
        for i in range(3):
            self.image.blit(self.SPRITE, (i * 32, 0))
        self.mask = pygame.mask.from_surface(self.image)
 
 
class Fruit(Object):
    ANIMATION_DELAY = 2
    SPRITES = load_sprite_sheets("Items", "Fruits", 32, 32)
    KINDS = ["Apple", "Orange", "Bananas", "Cherries", "Strawberry", "Kiwi", "Melon", "Pineapple"]
 
    def __init__(self, x, y, kind):
        super().__init__(x, y, 64, 64, "fruit")
        self.kind = kind
        self.animation_count = 0
 
    def loop(self):
        sprites = self.SPRITES[self.kind]
        self.image = sprites[(self.animation_count // self.ANIMATION_DELAY) % len(sprites)]
        self.animation_count += 1
 
 
class Enemy(Object):
    ANIMATION_DELAY = 3
    SPEED = 2
    SPRITES = {"rhino": load_sprite_sheets("Enemies", "Rino", 52, 34, True),
               "bat": load_sprite_sheets("Enemies", "Bat", 46, 30, True)}
    SHEET = {"rhino": "Run (52x34)", "bat": "Flying (46x30)"}
 
    def __init__(self, kind, x, y, left, right):
        width, height = self.SPRITES[kind][self.SHEET[kind] + "_left"][0].get_size()
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
        sprites = self.SPRITES[self.name][self.SHEET[self.name] + "_" + facing]
        self.image = sprites[(self.animation_count // self.ANIMATION_DELAY) % len(sprites)]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count += 1
 
 
class Flag(Object):
    ANIMATION_DELAY = 3
    SPRITES = load_sprite_sheets("Items", join("Checkpoints", "Checkpoint"), 64, 64)
 
    def __init__(self, x, y):
        super().__init__(x, y, 128, 128, "flag")
        self.image = self.SPRITES["Checkpoint (Flag Idle)(64x64)"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
 
    def loop(self):
        sprites = self.SPRITES["Checkpoint (Flag Idle)(64x64)"]
        self.image = sprites[(self.animation_count // self.ANIMATION_DELAY) % len(sprites)]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)
 
 
class Level:
    def __init__(self, number):
        data = LEVELS[number]
        self.length = data["length"] * BLOCK_SIZE
        self.background = data["background"]
 
        hole_columns = set()
        for start, width in data["holes"]:
            for column in range(start, start + width):
                hole_columns.add(column)
        self.blocks = [Block(c * BLOCK_SIZE, FLOOR_Y, BLOCK_SIZE)
                       for c in range(data["length"]) if c not in hole_columns]
 
        for column, height in data["blocks"]:
            self.blocks.append(Block(column * BLOCK_SIZE, FLOOR_Y - height * BLOCK_SIZE, BLOCK_SIZE))
 
        self.fruits = []
        for column, height in data["fruits"]:
            kind = Fruit.KINDS[(column + height) % len(Fruit.KINDS)]
            self.fruits.append(Fruit(column * BLOCK_SIZE + 16, FLOOR_Y - height * BLOCK_SIZE + 16, kind))
 
        self.enemies = []
        for column, left, right in data["rhinos"]:
            self.enemies.append(Enemy("rhino", column * BLOCK_SIZE + 12, FLOOR_Y - 68,
                                      left * BLOCK_SIZE, right * BLOCK_SIZE))
        for column, height, left, right in data["bats"]:
            self.enemies.append(Enemy("bat", column * BLOCK_SIZE, FLOOR_Y - height * BLOCK_SIZE + 18,
                                      left * BLOCK_SIZE, right * BLOCK_SIZE))
 
        self.traps = [Fire(c * BLOCK_SIZE + 32, FLOOR_Y - 64, 32, 64) for c in data["fires"]]
        self.traps += [Spikes(c * BLOCK_SIZE, FLOOR_Y - 32) for c in data["spikes"]]
 
        self.flag = Flag(data["flag"] * BLOCK_SIZE - 16, FLOOR_Y - 128)
        self.start = (BLOCK_SIZE + 16, FLOOR_Y - 70)
        self.total_fruits = len(self.fruits)
 
 
def get_background(name):
    image = pygame.image.load(join(ASSETS, "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []
 
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)
 
    return tiles, image
 
 
def draw_heart(surface, x, y, size, color):
    r = size // 4
    pygame.draw.circle(surface, color, (x + r, y + r), r)
    pygame.draw.circle(surface, color, (x + size - r, y + r), r)
    pygame.draw.polygon(surface, color, [(x, y + r), (x + size, y + r), (x + size // 2, y + size)])
 
 
def draw_text(window, text, size, center=None, topleft=None):
    font = pygame.font.Font(None, size)
    image = font.render(text, True, (255, 255, 255))
    rect = image.get_rect()
    if center:
        rect.center = center
    if topleft:
        rect.topleft = topleft
    window.blit(font.render(text, True, (0, 0, 0)), rect.move(2, 2))
    window.blit(image, rect)
 
 
def draw(window, background, bg_image, player, level, offset_x, score, lives, level_number):
    for tile in background:
        window.blit(bg_image, tile)
 
    for group in (level.blocks, level.traps, level.fruits, level.enemies):
        for obj in group:
            if obj.rect.right - offset_x > 0 and obj.rect.left - offset_x < WIDTH:
                obj.draw(window, offset_x)
    level.flag.draw(window, offset_x)
    player.draw(window, offset_x)
 
    bar = pygame.Surface((WIDTH, 60), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 120))
    window.blit(bar, (0, 0))
    for i in range(START_LIVES):
        color = (255, 60, 100) if i < lives else (90, 70, 80)
        draw_heart(window, 14 + i * 42, 14, 34, color)
    window.blit(pygame.transform.scale(Fruit.SPRITES["Apple"][0], (48, 48)), (200, 6))
    collected = level.total_fruits - len(level.fruits)
    draw_text(window, f"{collected}/{level.total_fruits}", 38, topleft=(252, 19))
    draw_text(window, f"Score {score}", 44, center=(560, 30))
    draw_text(window, f"Level {level_number + 1}", 40, topleft=(850, 18))
 
    pygame.display.update()
 
 
def show_text(window, title, score):
    window.fill((30, 30, 60))
    draw_text(window, title, 100, center=(WIDTH // 2, 330))
    draw_text(window, f"Score: {score}", 50, center=(WIDTH // 2, 430))
    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                waiting = False
    pygame.event.clear(pygame.KEYDOWN)
 
 
def handle_vertical_collision(player, objects, dy):
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
 
 
def collide(player, objects, dx):
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
 
 
def handle_move(player, objects):
    keys = pygame.key.get_pressed()
 
    player.x_vel = 0
 
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)
 
    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)
 
    handle_vertical_collision(player, objects, player.y_vel)
 
 
def hurt(player, lives):
    if player.hit:
        return lives
    player.make_hit()
    player.y_vel = -6
    player.fall_count = 0
    play_sound("hurt")
    return lives 
 
def play_level(window, level_number, score, lives):
    clock = pygame.time.Clock()
    level = Level(level_number)
    background, bg_image = get_background(level.background)
    player = Player(*level.start, 50, 50)
 
    offset_x = 0
    scroll_area_width = 200
 
    while True:
        clock.tick(FPS)
 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", score, lives
 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit", score, lives
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()
                    play_sound("jump")
 
        player.loop(FPS)
        for obj in level.traps + level.fruits + level.enemies + [level.flag]:
            obj.loop()
        handle_move(player, level.blocks)
 
        if player.rect.left < 0:
            player.rect.left = 0
        if player.rect.right > level.length:
            player.rect.right = level.length
 
        for trap in level.traps:
            if pygame.sprite.collide_mask(player, trap):
                lives = hurt(player, lives)
 
        for enemy in level.enemies[:]:
            if pygame.sprite.collide_mask(player, enemy):
                from_above = player.y_vel > 0 and player.rect.bottom <= enemy.rect.centery + 12
                if from_above:
                    level.enemies.remove(enemy)
                    player.bounce()
                    score += 100
                    play_sound("stomp")
                else:
                    lives = hurt(player, lives)
 
        for fruit in level.fruits[:]:
            if player.rect.colliderect(fruit.rect.inflate(-16, -16)):
                level.fruits.remove(fruit)
                score += 10
                play_sound("fruit")
 
        if player.rect.top > HEIGHT:
            lives -= 1
            play_sound("hurt")
            if lives > 0:
                player = Player(*level.start, 50, 50)
                player.make_hit()
                offset_x = 0
 
        if lives <= 0:
            return "dead", score, 0
 
        if pygame.sprite.collide_mask(player, level.flag):
            return "won", score + 100, lives
 
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel
        offset_x = max(0, min(offset_x, level.length - WIDTH))
 
        draw(window, background, bg_image, player, level, offset_x, score, lives, level_number)
 
 
def main(window):
    load_sounds()
 
    score = 0
    lives = START_LIVES
    level_number = 0
 
    while True:
        result, score, lives = play_level(window, level_number, score, lives)
 
        if result == "quit":
            break
 
        if result == "won":
            play_sound("win")
            level_number += 1
            if level_number == len(LEVELS):
                show_text(window, "YOU WIN!", score)
                score, lives, level_number = 0, START_LIVES, 0
 
        elif result == "dead":
            play_sound("lose")
            show_text(window, "GAME OVER", score)
            score, lives, level_number = 0, START_LIVES, 0
 
    pygame.quit()
    quit()
 
 
if __name__ == "__main__":
    main(window)
 