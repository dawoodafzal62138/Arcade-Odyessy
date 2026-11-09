"""Shared cabinet presentation and screen-to-game mouse coordinates."""
import pygame
from settigns import CURRENT_DIR


class ArcadeScreen:
    # Inner opening of the updated 1672 x 941 artwork, inside the neon border.
    GLASS = pygame.Rect(307, 213, 1059, 583)

    def __init__(self, size):
        artwork = pygame.image.load(
            CURRENT_DIR / 'resources' / 'Neon Cyberpunk Arcade Tileset2.png'
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


_cabinets = {}


def cabinet(screen):
    size = screen.get_size()
    if size not in _cabinets:
        _cabinets[size] = ArcadeScreen(size)
    return _cabinets[size]


def draw_arcade(screen, game, shake=(0, 0)):
    cabinet(screen).draw(screen, game, shake)


def arcade_mouse(screen, position, game_size):
    return cabinet(screen).to_game(position, game_size)
