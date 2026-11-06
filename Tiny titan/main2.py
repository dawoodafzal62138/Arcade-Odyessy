import math
import os
import random
from array import array
from os import listdir
from os.path import isfile, join

import pygame

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
BLOCK_SIZE = 96
# Every level is 8 rows of blocks high. The top row starts at y = TOP, so the
# bottom row (the floor) ends up at y = HEIGHT - BLOCK_SIZE, same as the tutorial.
TOP = HEIGHT - 8 * BLOCK_SIZE
START_LIVES = 3
MAX_LIVES = 5

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = join(BASE_DIR, "assets")
HS_FILE = join(BASE_DIR, "highscore.txt")

# The display has to exist before we load images, because convert_alpha() needs it.
# (That's why this line is up here and not inside main like you might expect.)
window = pygame.display.set_mode((WIDTH, HEIGHT))

# ----------------------------------------------------------------------------
# LEVELS - each one is an 8-row map, the last row is the floor.
#   #  block          P  player start       G  trophy (end of level)
#   F  fruit          H  extra heart        E  pig enemy (walks on the floor)
#   B  bat enemy      f  fire trap          ^  spikes          S  saw blade
# A gap in the floor row is a pit - fall in and you lose a heart.
# ----------------------------------------------------------------------------
LEVELS = [
    {
        "name": "Level 1",
        "background": "Blue.png",
        "rows": [
            "                                            ",
            "                                            ",
            "                                            ",
            "                                            ",
            "                                   FF       ",
            "              FF   FF       FF     ##       ",
            " P F F  f  EF    F ##   E F     F##     G   ",
            "##############  ############  ##############",
        ],
    },
    {
        "name": "Level 2",
        "background": "Green.png",
        "rows": [
            "                                                          ",
            "                                                          ",
            "                                                          ",
            "                                                          ",
            "                     HF                    FF         B   ",
            "     F      FF  F B  ##  FF FF      F FF   ##  FF F       ",
            " P F ^   E F   Ff  ##       ^^  E  f     ##  F    ^ EF  G ",
            "############  ###########  ###########  #######  #########",
        ],
    },
    {
        "name": "Level 3",
        "background": "Purple.png",
        "rows": [
            "                                                                      ",
            "                                                                      ",
            "                                                                      ",
            "                                                    F                 ",
            "                B          FH         B           FF#                 ",
            "    F     FF      FF  FF   ##    FF F    FF  FF   ##     FF   FF F    ",
            " P Ff  E     F S  ^^ F   ##    E    f  E ^^     ##     F    E ^^ f  G ",
            "##########  ##########  #########  ##########  ##########  ###########",
        ],
    },
]


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    # Loads EVERY png inside assets/dir1/dir2 and cuts each one into frames of
    # width x height. That's why all the pngs in a folder need the same frame size.
    # With direction=True we also keep a flipped copy of every frame so the
    # character can face left or right ("idle_left", "idle_right", ...).
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
    # Terrain.png is one big picture with lots of tiles. The grass block we want
    # starts at x=96, y=0, so we cut that piece out and double its size.
    path = join(ASSETS, "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


# ----------------------------------------------------------------------------
# Sound - the asset pack has no audio, so we build little beeps from sine /
# square waves. Nothing to download and it just works.
# ----------------------------------------------------------------------------
class Sfx:
    def __init__(self):
        self.muted = False
        self.sounds = {}
        self.ok = pygame.mixer.get_init() is not None  # no sound card? then stay silent
        if self.ok:
            self.channels = pygame.mixer.get_init()[2]
            self._build()

    def _make(self, notes, wave="square", vol=0.25):
        # notes = list of (start frequency, end frequency, seconds). The pitch
        # slides from start to end, and the volume fades out over each note.
        rate = 44100
        buf = array("h")
        for f0, f1, dur in notes:
            n = int(rate * dur)
            phase = 0.0
            for i in range(n):
                t = i / n
                phase += (f0 + (f1 - f0) * t) / rate
                if wave == "square":
                    s = 1.0 if (phase % 1) < 0.5 else -1.0
                elif wave == "noise":
                    s = random.uniform(-1, 1)
                else:
                    s = math.sin(2 * math.pi * phase)
                value = int(s * (1 - t) * vol * 32767)
                for _ in range(self.channels):
                    buf.append(value)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _build(self):
        try:
            self.sounds = {
                "jump": self._make([(300, 650, 0.15)]),
                "fruit": self._make([(988, 988, 0.05), (1319, 1319, 0.09)], "sine", 0.35),
                "stomp": self._make([(260, 90, 0.14)], "noise", 0.35),
                "hurt": self._make([(420, 90, 0.35)]),
                "heart": self._make([(523, 523, 0.08), (659, 659, 0.08), (784, 784, 0.12)], "sine", 0.35),
                "level": self._make([(523, 523, 0.1), (659, 659, 0.1), (784, 784, 0.1),
                                     (1046, 1046, 0.3)], "square", 0.2),
                "over": self._make([(400, 400, 0.2), (330, 330, 0.2), (250, 250, 0.2),
                                    (180, 180, 0.5)]),
                "win": self._make([(523, 523, 0.12), (659, 659, 0.12), (784, 784, 0.12),
                                   (1046, 1046, 0.12), (784, 784, 0.12), (1046, 1046, 0.4)],
                                  "square", 0.2),
            }
        except pygame.error:
            self.ok = False

    def play(self, name):
        if self.ok and not self.muted and name in self.sounds:
            self.sounds[name].play()


# ----------------------------------------------------------------------------
# Player (the tutorial one, plus a few things for lives / bouncing / respawn)
# ----------------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.safe_point = (x, y)  # where we put the player back after falling in a pit

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def bounce(self):
        # Used after stomping an enemy. Counts like a first jump, so you can
        # still double-jump off an enemy's head.
        self.y_vel = -self.GRAVITY * 8
        self.fall_count = 0
        self.jump_count = 1

    def respawn(self):
        self.rect.x, self.rect.y = self.safe_point
        self.x_vel = self.y_vel = 0
        self.fall_count = 0
        self.jump_count = 0
        self.make_hit()  # a couple of seconds of "can't be hurt" after coming back

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
        # Gravity isn't constant: it starts tiny and grows as fall_count goes up
        # (capped at 1 per frame). That gives the nice floaty feel at the top of
        # a jump and a faster drop later. fall_count resets whenever we land.
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        # "hit" doubles as our invincibility timer: for 2 seconds nothing can hurt us
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
        # Pick which sprite sheet to show, in priority order: hit > jumping >
        # falling > running > standing still.
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
        # Rebuild the rect + mask from the current picture. The mask is what makes
        # collisions pixel-perfect instead of using a boring box.
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


# ----------------------------------------------------------------------------
# Objects: blocks, traps, pickups, enemies, trophy
# ----------------------------------------------------------------------------
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


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size, "block")
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    """The tutorial fire, but it switches itself on and off so you can time your jump."""
    ANIMATION_DELAY = 3
    ON_TIME = 120   # frames the flames stay on
    OFF_TIME = 100  # frames they stay off
    SPRITES = load_sprite_sheets("Traps", "Fire", 16, 32)

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = self.SPRITES
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"
        self.timer = random.randint(0, self.OFF_TIME)  # so the fires aren't all in sync

    @property
    def harmful(self):
        return self.animation_name == "on"  # only burns while the flames are showing

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        self.timer += 1
        if self.animation_name == "off" and self.timer >= self.OFF_TIME:
            self.on()
            self.timer = 0
        elif self.animation_name == "on" and self.timer >= self.ON_TIME:
            self.off()
            self.timer = 0

        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        # keep the bottom of the fire on the floor even if the picture changes size
        bottom = self.rect.bottom
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.rect.bottom = bottom
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Spikes(Object):
    """A row of 3 little spikes across one block. Always dangerous, just jump over."""
    SPRITE = pygame.transform.scale2x(
        pygame.image.load(join(ASSETS, "Traps", "Spikes", "Idle.png")).convert_alpha())
    harmful = True

    def __init__(self, x, y):
        super().__init__(x, y, BLOCK_SIZE, 32, "spikes")
        for i in range(3):
            self.image.blit(self.SPRITE, (i * 32, 0))
        self.mask = pygame.mask.from_surface(self.image)

    def loop(self):
        pass


class Saw(Object):
    """A saw blade that slides left and right along the floor."""
    ANIMATION_DELAY = 2
    SPRITES = load_sprite_sheets("Traps", "Saw", 38, 38)
    harmful = True

    def __init__(self, x, y):
        super().__init__(x, y, 76, 76, "saw")
        self.start_x = x
        self.vel = 2
        self.range = 110  # how far it travels each way, in pixels
        self.animation_count = 0

    def loop(self):
        self.rect.x += self.vel
        if abs(self.rect.x - self.start_x) >= self.range:
            self.vel *= -1  # hit the end of its track, go back

        sprites = self.SPRITES["on"]
        self.image = sprites[(self.animation_count // self.ANIMATION_DELAY) % len(sprites)]
        self.animation_count += 1
        self.mask = pygame.mask.from_surface(self.image)


class Fruit(Object):
    ANIMATION_DELAY = 2
    SPRITES = load_sprite_sheets("Items", "Fruits", 32, 32)
    KINDS = ["Apple", "Orange", "Bananas", "Cherries", "Strawberry", "Kiwi", "Melon", "Pineapple"]

    def __init__(self, x, y, kind):
        super().__init__(x, y, 64, 64, "fruit")
        self.kind = kind
        self.animation_count = random.randint(0, 30)
        self.collected = False
        self.done = False  # becomes True when the "pop" animation has finished

    def collect(self):
        self.collected = True
        self.animation_count = 0

    def loop(self):
        name = "Collected" if self.collected else self.kind
        sprites = self.SPRITES[name]
        index = self.animation_count // self.ANIMATION_DELAY
        if self.collected and index >= len(sprites):
            self.done = True
            return
        self.image = sprites[index % len(sprites)]
        self.animation_count += 1


class Heart(Object):
    """Extra life pickup. We draw it ourselves since the pack has no heart sprite."""
    SPRITE = None

    def __init__(self, x, y):
        super().__init__(x, y, 48, 48, "heart")
        self.base_y = y
        self.t = random.random() * 6
        if Heart.SPRITE is None:
            Heart.SPRITE = pygame.Surface((48, 48), pygame.SRCALPHA)
            draw_heart(Heart.SPRITE, 4, 6, 40, (255, 60, 100))
        self.image = Heart.SPRITE
        self.mask = pygame.mask.from_surface(self.image)

    def loop(self):
        self.t += 0.08
        self.rect.y = self.base_y + int(math.sin(self.t) * 5)  # gentle floating


class Pig(Object):
    """Walks back and forth on the floor. Turns around at walls, traps and edges."""
    ANIMATION_DELAY = 3
    SPEED = 2
    SPRITES = load_sprite_sheets("Enemies", "AngryPig", 36, 30, True)
    HIT_FRAMES = 5

    def __init__(self, x, y):
        super().__init__(x, y, 72, 60, "pig")
        self.vel = -self.SPEED
        self.animation_count = 0
        self.dying = False
        self.dead = False
        self.image = self.SPRITES["Walk (36x30)_right"][0]
        self.mask = pygame.mask.from_surface(self.image)

    def die(self):
        self.dying = True
        self.animation_count = 0

    def loop(self, level):
        if not self.dying:
            # Look a few pixels in front of us. If there's a wall there, or no
            # floor under that spot, we're about to bump or fall, so turn around.
            front_x = self.rect.right + 4 if self.vel > 0 else self.rect.left - 4
            col = front_x // BLOCK_SIZE
            body_row = (self.rect.centery - TOP) // BLOCK_SIZE
            floor_row = (self.rect.bottom + 4 - TOP) // BLOCK_SIZE
            wall = (col, body_row) in level.enemy_walls
            no_floor = (col, floor_row) not in level.cells
            if wall or no_floor:
                self.vel *= -1
            self.rect.x += self.vel

        # The pig artwork faces LEFT by default, but load_sprite_sheets assumes art
        # faces right. So the names are swapped: "_right" = looking left here.
        facing = "right" if self.vel < 0 else "left"
        sheet = "Hit 1 (36x30)" if self.dying else "Walk (36x30)"
        sprites = self.SPRITES[sheet + "_" + facing]
        delay = 4 if self.dying else self.ANIMATION_DELAY
        index = self.animation_count // delay
        if self.dying and index >= len(sprites):
            self.dead = True
            return
        self.image = sprites[index % len(sprites)]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count += 1


class Bat(Object):
    """Flies in a lazy wave. Hard to hit from below, easy to stomp from above."""
    ANIMATION_DELAY = 3
    SPRITES = load_sprite_sheets("Enemies", "Bat", 46, 30, True)

    def __init__(self, x, y):
        super().__init__(x, y, 92, 60, "bat")
        self.start_x = x
        self.base_y = y
        self.t = random.random() * 6
        self.animation_count = 0
        self.dying = False
        self.dead = False
        self.facing = "left"
        self.image = self.SPRITES["Flying (46x30)_right"][0]
        self.mask = pygame.mask.from_surface(self.image)

    def die(self):
        self.dying = True
        self.animation_count = 0

    def loop(self, level):
        if not self.dying:
            self.t += 0.03
            # x swings left-right with sin, y bobs up and down at a different speed,
            # which makes the path look like a wobbly figure instead of a straight line
            self.rect.x = self.start_x + int(math.sin(self.t) * 150)
            self.rect.y = self.base_y + int(math.sin(self.t * 2.3) * 30)
            self.facing = "right" if math.cos(self.t) < 0 else "left"  # art faces left, see Pig

        sheet = "Hit (46x30)" if self.dying else "Flying (46x30)"
        sprites = self.SPRITES[sheet + "_" + self.facing]
        delay = 4 if self.dying else self.ANIMATION_DELAY
        index = self.animation_count // delay
        if self.dying and index >= len(sprites):
            self.dead = True
            return
        self.image = sprites[index % len(sprites)]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count += 1


class Trophy(Object):
    """The end of the level. Touch it and it plays its 'pressed' animation."""
    SPRITES = load_sprite_sheets("Items", join("Checkpoints", "End"), 64, 64)

    def __init__(self, x, y):
        super().__init__(x, y, 128, 128, "trophy")
        self.pressed = False
        self.animation_count = 0
        self.image = self.SPRITES["End (Idle)"][0]
        self.mask = pygame.mask.from_surface(self.image)

    def press(self):
        self.pressed = True
        self.animation_count = 0

    def loop(self):
        if self.pressed:
            sprites = self.SPRITES["End (Pressed) (64x64)"]
            index = min(self.animation_count // 6, len(sprites) - 1)  # play once, then hold
            self.image = sprites[index]
            self.animation_count += 1


# ----------------------------------------------------------------------------
# Level: turns the ASCII map into real objects
# ----------------------------------------------------------------------------
class Level:
    def __init__(self, index):
        data = LEVELS[index]
        self.index = index
        self.name = data["name"]
        self.background, self.bg_image = get_background(data["background"])

        self.blocks = []     # things you can stand on / bump into
        self.traps = []      # fire, spikes, saws
        self.fruits = []
        self.hearts = []
        self.enemies = []
        self.trophy = None
        self.player_start = (100, 100)
        # Pigs need to know where walls and edges are. These two sets of (col, row)
        # cells let them check that quickly without testing every block.
        self.cells = set()
        self.enemy_walls = set()

        rows = data["rows"]
        for r, line in enumerate(rows):
            for c, ch in enumerate(line):
                x = c * BLOCK_SIZE
                y = TOP + r * BLOCK_SIZE
                bottom = y + BLOCK_SIZE
                if ch == "#":
                    self.blocks.append(Block(x, y, BLOCK_SIZE))
                    self.cells.add((c, r))
                    self.enemy_walls.add((c, r))
                elif ch == "P":
                    self.player_start = (x + 16, bottom - 64 - 2)
                elif ch == "F":
                    kind = Fruit.KINDS[(c + r) % len(Fruit.KINDS)]
                    self.fruits.append(Fruit(x + 16, y + 16, kind))
                elif ch == "H":
                    self.hearts.append(Heart(x + 24, y + 24))
                elif ch == "E":
                    self.enemies.append(Pig(x + 12, bottom - 60))
                elif ch == "B":
                    self.enemies.append(Bat(x + 2, y + 18))
                elif ch == "f":
                    self.traps.append(Fire(x + 32, bottom - 64, 32, 64))
                    self.enemy_walls.add((c, r))
                elif ch == "^":
                    self.traps.append(Spikes(x, bottom - 32))
                    self.enemy_walls.add((c, r))
                elif ch == "S":
                    self.traps.append(Saw(x + 10, bottom - 76))
                elif ch == "G":
                    self.trophy = Trophy(x - 16, bottom - 128)

        self.width_px = len(rows[0]) * BLOCK_SIZE
        self.total_fruits = len(self.fruits)
        self.collected = 0


class Session:
    """Everything that carries over between frames: score, lives, which screen we're on."""

    def __init__(self):
        self.score = 0
        self.lives = START_LIVES
        self.state = "menu"   # menu, playing, goal, level_done, game_over, win
        self.goal_timer = 0
        self.high_score = self.load_high_score()

    def load_high_score(self):
        try:
            with open(HS_FILE) as f:
                return int(f.read().strip())
        except (OSError, ValueError):
            return 0

    def save_high_score(self):
        if self.score > self.high_score:
            self.high_score = self.score
            try:
                with open(HS_FILE, "w") as f:
                    f.write(str(self.high_score))
            except OSError:
                pass


# ----------------------------------------------------------------------------
# Drawing
# ----------------------------------------------------------------------------
def draw_heart(surf, x, y, size, color, filled=True):
    r = size // 4
    pts = [(x, y + r), (x + size, y + r), (x + size // 2, y + size)]
    width = 0 if filled else 2
    pygame.draw.circle(surf, color, (x + r, y + r), r, width)
    pygame.draw.circle(surf, color, (x + size - r, y + r), r, width)
    if filled:
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.circle(surf, (255, 190, 200), (x + r - 1, y + r - 2), max(1, r // 3))
    else:
        pygame.draw.lines(surf, color, False, [(x + 1, y + r + 2), (x + size // 2, y + size - 1),
                                               (x + size - 1, y + r + 2)], 2)


def draw_text(surf, text, size, color, center=None, topleft=None):
    font = pygame.font.Font(None, size)
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = center
    if topleft:
        rect.topleft = topleft
    surf.blit(font.render(text, True, (0, 0, 0)), rect.move(2, 2))  # little shadow
    surf.blit(img, rect)


def get_background(name):
    image = pygame.image.load(join(ASSETS, "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def on_screen(obj, offset_x):
    # Skip drawing anything that's outside the window, saves a lot of work on long levels
    return obj.rect.right - offset_x > 0 and obj.rect.left - offset_x < WIDTH


def draw_hud(window, level, session):
    bar = pygame.Surface((WIDTH, 62), pygame.SRCALPHA)
    bar.fill((0, 0, 0, 120))
    window.blit(bar, (0, 0))
    for i in range(max(START_LIVES, session.lives)):
        draw_heart(window, 14 + i * 42, 14, 34, (255, 60, 100), filled=i < session.lives)
    icon = pygame.transform.scale(Fruit.SPRITES["Apple"][0], (48, 48))
    window.blit(icon, (330, 7))
    draw_text(window, f"{level.collected}/{level.total_fruits}", 38, (255, 255, 255), topleft=(382, 20))
    draw_text(window, f"Score {session.score}", 44, (255, 235, 120), center=(620, 32))
    draw_text(window, f"{level.name}", 36, (255, 255, 255), topleft=(800, 8))
    draw_text(window, f"Best {session.high_score}", 28, (220, 220, 220), topleft=(800, 36))


def overlay(window, title, lines, color=(255, 255, 255)):
    shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 150))
    window.blit(shade, (0, 0))
    draw_text(window, title, 100, color, center=(WIDTH // 2, 250))
    for i, line in enumerate(lines):
        draw_text(window, line, 40, (255, 255, 255), center=(WIDTH // 2, 350 + i * 46))


def draw(window, level, player, session, sfx, offset_x):
    for tile in level.background:
        window.blit(level.bg_image, tile)

    for group in (level.blocks, level.traps, level.fruits, level.hearts, level.enemies):
        for obj in group:
            if on_screen(obj, offset_x):
                obj.draw(window, offset_x)
    level.trophy.draw(window, offset_x)
    player.draw(window, offset_x)

    if session.state != "menu":
        draw_hud(window, level, session)
    if sfx.muted:
        draw_text(window, "MUTED", 26, (255, 120, 120), topleft=(WIDTH - 84, 68))

    if session.state == "menu":
        overlay(window, "FRUIT RUN", [
            "Collect fruits, stomp enemies, reach the trophy!",
            "Arrows / A D = move     Space / W / Up = jump (twice = double jump)",
            "Watch out for fire, spikes and saws.     M = mute",
            f"Best score: {session.high_score}",
            "Press ENTER to start"], (255, 220, 90))
    elif session.state == "level_done":
        overlay(window, "LEVEL COMPLETE!", [
            f"Fruits: {level.collected}/{level.total_fruits}",
            f"Score: {session.score}",
            "Press ENTER for the next level"], (120, 255, 140))
    elif session.state == "game_over":
        overlay(window, "GAME OVER", [
            f"Final score: {session.score}",
            f"Best score: {session.high_score}",
            "Press ENTER to try again"], (255, 90, 90))
    elif session.state == "win":
        overlay(window, "YOU WIN!", [
            "You finished all 3 levels!",
            f"Final score: {session.score}",
            f"Best score: {session.high_score}",
            "Press ENTER to play again"], (255, 220, 90))

    pygame.display.update()


# ----------------------------------------------------------------------------
# Collisions (same idea as the tutorial)
# ----------------------------------------------------------------------------
def nearby(player, objects, reach=300):
    # Checking pixel masks against every block in a 70-block level, every frame,
    # gets slow. Most blocks are miles away, so only look at the ones close by.
    px, py = player.rect.center
    return [o for o in objects if abs(o.rect.centerx - px) < reach and abs(o.rect.centery - py) < reach]


def handle_vertical_collision(player, objects, dy):
    # Called after the player has already moved down/up this frame. If we ended up
    # inside a block, snap back out of it: onto the top when falling (dy > 0),
    # or against the bottom when we bonk our head (dy < 0).
    collided_objects = []
    for obj in nearby(player, objects):
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
    # "What if I moved dx pixels sideways - would I hit something?" We really move
    # the player, test, then move straight back. The player never visibly moves,
    # we just learn whether there's a wall dx pixels away.
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in nearby(player, objects):
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, level):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    # Look 10px to each side. If there's a block there we're not allowed to walk
    # that way (this is what stops you from walking into walls).
    collide_left = collide(player, level.blocks, -PLAYER_VEL * 2)
    collide_right = collide(player, level.blocks, PLAYER_VEL * 2)

    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collide_left:
        player.move_left(PLAYER_VEL)
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collide_right:
        player.move_right(PLAYER_VEL)

    handle_vertical_collision(player, level.blocks, player.y_vel)

    # Don't let the player walk out of the level on either side
    if player.rect.left < 0:
        player.rect.left = 0
    if player.rect.right > level.width_px:
        player.rect.right = level.width_px


def remember_safe_spot(player, level):
    # If we're standing on solid ground that has ground on both sides too, it's a
    # decent place to come back to after falling into a pit. (We don't want to
    # respawn on the very edge of a hole and instantly fall again.)
    if player.jump_count == 0 and player.y_vel == 0:
        col = player.rect.centerx // BLOCK_SIZE
        row = (player.rect.bottom - TOP) // BLOCK_SIZE
        if (col, row) in level.cells and (col - 1, row) in level.cells and (col + 1, row) in level.cells:
            player.safe_point = (player.rect.x, player.rect.y)


# ----------------------------------------------------------------------------
# Game rules
# ----------------------------------------------------------------------------
def hurt_player(player, session, sfx):
    if player.hit:  # still in the 2-second grace period
        return
    player.make_hit()
    player.y_vel = -6  # little hop so you can see you got hit
    player.fall_count = 0
    session.lives -= 1
    sfx.play("hurt")
    if session.lives <= 0:
        session.save_high_score()
        sfx.play("over")
        session.state = "game_over"


def check_interactions(player, level, session, sfx):
    """Traps, enemies, fruit, hearts and the trophy. Called once per frame."""
    # --- traps ---
    for trap in nearby(player, level.traps):
        if trap.harmful and pygame.sprite.collide_mask(player, trap):
            hurt_player(player, session, sfx)

    # --- enemies ---
    for enemy in nearby(player, level.enemies):
        if enemy.dying or not pygame.sprite.collide_mask(player, enemy):
            continue
        # It's a stomp if we're falling and our feet are in the top part of the
        # enemy. Anything else (running into it, jumping into it from below) hurts.
        stomping = player.y_vel > 0 and player.rect.bottom <= enemy.rect.centery + 12
        if stomping:
            enemy.die()
            player.bounce()
            session.score += 100
            sfx.play("stomp")
        else:
            hurt_player(player, session, sfx)

    # --- pickups ---
    for fruit in nearby(player, level.fruits):
        if not fruit.collected and player.rect.colliderect(fruit.rect.inflate(-16, -16)):
            fruit.collect()
            level.collected += 1
            session.score += 10
            sfx.play("fruit")
    for heart in nearby(player, level.hearts):
        if pygame.sprite.collide_mask(player, heart):
            level.hearts.remove(heart)
            sfx.play("heart")
            if session.lives < MAX_LIVES:
                session.lives += 1
            else:
                session.score += 50  # already full of hearts, so take points instead

    # --- the end ---
    if session.state == "playing" and pygame.sprite.collide_mask(player, level.trophy):
        level.trophy.press()
        session.score += 100 + 25 * session.lives  # bonus for finishing with hearts left
        session.save_high_score()
        last_level = level.index == len(LEVELS) - 1
        sfx.play("win" if last_level else "level")
        session.state = "goal"
        session.goal_timer = 70  # let the trophy animation play before the next screen


def update_objects(level):
    for trap in level.traps:
        trap.loop()
    for fruit in level.fruits:
        fruit.loop()
    level.fruits = [f for f in level.fruits if not f.done]
    for heart in level.hearts:
        heart.loop()
    for enemy in level.enemies:
        enemy.loop(level)
    level.enemies = [e for e in level.enemies if not e.dead]
    level.trophy.loop()


def start_level(index):
    level = Level(index)
    player = Player(*level.player_start, 50, 50)
    player.safe_point = level.player_start
    player.update_sprite()
    return level, player


def camera_for(player, level):
    # Put the player in the middle of the screen, but never show past the ends of the level
    return max(0, min(player.rect.centerx - WIDTH // 2, level.width_px - WIDTH))


def main(window):
    clock = pygame.time.Clock()
    sfx = Sfx()
    session = Session()
    level, player = start_level(0)

    offset_x = 0
    scroll_area_width = 250  # the camera only starts moving when you get this close to a screen edge

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                elif event.key == pygame.K_m:
                    sfx.muted = not sfx.muted
                elif event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    if session.state == "playing" and player.jump_count < 2:
                        player.jump()
                        sfx.play("jump")
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if session.state in ("menu", "game_over", "win"):
                        session.score, session.lives = 0, START_LIVES
                        level, player = start_level(0)
                        session.state = "playing"
                        offset_x = 0
                    elif session.state == "level_done":
                        level, player = start_level(level.index + 1)
                        session.state = "playing"
                        offset_x = 0

        if session.state == "playing":
            player.loop(FPS)
            update_objects(level)
            handle_move(player, level)
            remember_safe_spot(player, level)
            check_interactions(player, level, session, sfx)

            # Fell down a pit?
            if session.state == "playing" and player.rect.top > HEIGHT + 100:
                session.lives -= 1
                sfx.play("hurt")
                if session.lives <= 0:
                    session.save_high_score()
                    sfx.play("over")
                    session.state = "game_over"
                else:
                    player.respawn()
                    offset_x = camera_for(player, level)

            # Scrolling, tutorial style: only move the camera when the player pushes
            # into the left/right edge zone, then clamp so we never show empty space.
            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel
            offset_x = max(0, min(offset_x, level.width_px - WIDTH))

        elif session.state == "goal":
            # trophy animation plays, everything else holds still
            level.trophy.loop()
            session.goal_timer -= 1
            if session.goal_timer <= 0:
                session.state = "win" if level.index == len(LEVELS) - 1 else "level_done"

        draw(window, level, player, session, sfx, offset_x)

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)