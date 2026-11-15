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


_entry_frame = None
_entry_started = None
_entry_glass = None
_entry_foreground = None


def begin_game_transition(snapshot, glass, foreground=None):
    """Start the camera move when the first live game frame is available."""
    global _entry_frame, _entry_started, _entry_glass, _entry_foreground
    _entry_frame = snapshot.copy()
    _entry_foreground = foreground.copy() if foreground is not None else None
    _entry_glass = pygame.FRect(glass)
    _entry_started = None


def clear_game_transition():
    global _entry_frame, _entry_started, _entry_glass, _entry_foreground
    _entry_frame = None
    _entry_started = None
    _entry_glass = None
    _entry_foreground = None


_paused_game_ms = 0


def entry_transition_pending():
    return _entry_frame is not None


def game_ticks():
    """Gameplay time excludes time spent in the cabinet entry animation."""
    return pygame.time.get_ticks() - _paused_game_ms


def draw_arcade(screen, game, shake=(0, 0), cabinet_class=ArcadeScreen, clock=None):
    global _paused_game_ms
    if _entry_frame is not None:
        # Render a frozen first frame while the camera moves. The game loop
        # cannot advance physics, enemies, or input until this function returns.
        frozen = game.copy()
        started = pygame.time.get_ticks()
        transition_clock = pygame.time.Clock()
        while _entry_frame is not None:
            quit_events = pygame.event.get(pygame.QUIT)
            if quit_events:
                clear_game_transition()
                for event in quit_events:
                    pygame.event.post(event)
                break
            # Discard gameplay key presses made during the animation.
            pygame.event.get([pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEBUTTONDOWN,
                              pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL])
            _draw_arcade_frame(screen, frozen, shake, cabinet_class)
            pygame.display.flip()
            transition_clock.tick(60)
        _paused_game_ms += pygame.time.get_ticks() - started
        if clock is not None:
            clock.tick()
    _draw_arcade_frame(screen, game, shake, cabinet_class)


def _draw_arcade_frame(screen, game, shake=(0, 0), cabinet_class=ArcadeScreen):
    global _entry_started
    presentation = cabinet(screen, cabinet_class)
    presentation.draw(screen, game, shake)
    if _entry_frame is None:
        return
    now = pygame.time.get_ticks()
    if _entry_started is None:
        _entry_started = now
    progress = min(1.0, (now - _entry_started) / 1100)
    if progress >= 1:
        clear_game_transition()
        return
    eased = progress * progress * (3 - 2 * progress)
    viewport = presentation.viewport(game.get_size())
    full = pygame.FRect(screen.get_rect())
    # Align the zoomed cabinet glass with the final game viewport.
    scale = viewport.width / _entry_glass.width
    target = pygame.FRect(_entry_glass.x - viewport.x / scale,
                         _entry_glass.y - viewport.y / scale,
                         full.width / scale, full.height / scale)
    view = pygame.FRect(*(start + (end - start) * eased
                         for start, end in zip(full, target)))
    crop = pygame.Rect(round(view.x), round(view.y),
                       max(1, round(view.width)), max(1, round(view.height)))
    frame = pygame.Surface(crop.size)
    frame.blit(_entry_frame, (0, 0), crop)
    hub = pygame.transform.smoothscale(frame, screen.get_size())
    # Reveal the game cabinet around the growing playfield near the end.
    reveal = max(0.0, (progress - 0.6) / 0.4)
    reveal = reveal * reveal * (3 - 2 * reveal)
    hub.set_alpha(round(255 * (1 - reveal)))
    screen.blit(hub, (0, 0))
    sx, sy = full.width / view.width, full.height / view.height
    destination = pygame.Rect(round((_entry_glass.x - view.x) * sx),
                              round((_entry_glass.y - view.y) * sy),
                              max(1, round(_entry_glass.width * sx)),
                              max(1, round(_entry_glass.height * sy)))
    live = pygame.transform.smoothscale(game, destination.size)
    # Fade the live picture into the glass without hiding the wizard first.
    fade = min(1.0, progress / 0.22)
    live.set_alpha(round(255 * fade * fade * (3 - 2 * fade)))
    screen.blit(live, destination)
    if _entry_foreground is not None and reveal < 1:
        # Preserve depth: the wizard occludes the cabinet glass during the zoom.
        foreground_crop = pygame.Surface(crop.size, pygame.SRCALPHA)
        foreground_crop.blit(_entry_foreground, (0, 0), crop)
        foreground = pygame.transform.smoothscale(foreground_crop, screen.get_size())
        foreground.set_alpha(round(255 * (1 - reveal)))
        screen.blit(foreground, (0, 0))


def arcade_mouse(screen, position, game_size):
    return cabinet(screen).to_game(position, game_size)
