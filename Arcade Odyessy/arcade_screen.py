"""Shared cabinet presentation and screen-to-game mouse coordinates."""
import pygame
import math
from settigns import CURRENT_DIR


def cover_background(image, size):
    """Return an opaque background covering size with uniform scaling."""
    scale = max(size[0] / image.get_width(), size[1] / image.get_height())
    scaled = pygame.transform.scale(image, (math.ceil(image.get_width() * scale),
                                            math.ceil(image.get_height() * scale)))
    background = pygame.Surface(size)
    background.blit(scaled, scaled.get_rect(center=background.get_rect().center))
    return background


def arcade_game_size(width, height, cabinet_class=None):
    """Expand a playfield to the cabinet aspect ratio without shrinking it."""
    cabinet_class = cabinet_class or ArcadeScreen
    ratio = cabinet_class.GLASS.width / cabinet_class.GLASS.height
    if width / height < ratio:
        width = round(height * ratio)
    else:
        height = round(width / ratio)
    return width, height


class ArcadeScreen:
    # Inner opening of the updated 1672 x 941 artwork, inside the neon border.
    GLASS = pygame.Rect(307, 213, 1059, 583)
    ARTWORK = 'Neon Cyberpunk Arcade Tileset2.png'

    def __init__(self, size):
        artwork = pygame.image.load(
            CURRENT_DIR / 'resources' / self.ARTWORK
        ).convert()
        bounds = artwork.get_rect().fit(pygame.Rect((0, 0), size))
        self.background = pygame.Surface(size)
        self.background.fill((3, 8, 8))
        self.background.blit(pygame.transform.smoothscale(artwork, bounds.size), bounds)
        sx, sy = bounds.width / artwork.get_width(), bounds.height / artwork.get_height()
        self.glass = pygame.Rect(bounds.x + round(self.GLASS.x * sx),
                                 bounds.y + round(self.GLASS.y * sy),
                                 round(self.GLASS.width * sx), round(self.GLASS.height * sy))

    def viewport(self, game_size):
        # Native playfields match the opening; preserve sprite proportions.
        return pygame.Rect((0, 0), game_size).fit(self.glass)

    def draw(self, screen, game, shake=(0, 0)):
        screen.blit(self.background, (0, 0))
        viewport = self.viewport(game.get_size())
        old_clip = screen.get_clip()
        screen.set_clip(viewport)
        offset = (round(shake[0] * viewport.width / game.get_width()),
                  round(shake[1] * viewport.height / game.get_height()))
        screen.blit(pygame.transform.smoothscale(game, viewport.size), viewport.move(offset))
        screen.set_clip(old_clip)

    def to_game(self, position, game_size):
        viewport = self.viewport(game_size)
        return ((position[0] - viewport.x) * game_size[0] / viewport.width,
                (position[1] - viewport.y) * game_size[1] / viewport.height)


class NinjaArcadeScreen(ArcadeScreen):
    # Larger opening inside the green border of the 1671 x 941 version 2 art.
    GLASS = pygame.Rect(211, 152, 1248, 670)
    ARTWORK = 'Neon Cyberpunk Arcade Tileset2_version2.png'


_cabinets = {}


def cabinet(screen, cabinet_class=ArcadeScreen):
    size = screen.get_size()
    key = (size, cabinet_class)
    if key not in _cabinets:
        _cabinets[key] = cabinet_class(size)
    return _cabinets[key]


def draw_arcade(screen, game, shake=(0, 0), cabinet_class=ArcadeScreen):
    cabinet(screen, cabinet_class).draw(screen, game, shake)


def arcade_mouse(screen, position, game_size):
    return cabinet(screen).to_game(position, game_size)
