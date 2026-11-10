"""Arcade title and loading screens built from the game's existing artwork."""
import math
import pygame
from settigns import CURRENT_DIR


class StartupScreen:
    def __init__(self, screen):
        self.screen = screen
        self.canvas = pygame.Surface((1920, 1080))
        artwork = pygame.image.load(CURRENT_DIR / 'resources' / 'Neon Cyberpunk Arcade Tileset2.png').convert()
        self.background = pygame.transform.smoothscale(artwork, self.canvas.get_size())
        font_path = CURRENT_DIR.parent / 'space shooter' / 'images' / 'Oxanium-Bold.ttf'
        self.fonts = {size: pygame.font.Font(str(font_path), size) for size in (18, 22, 28, 36, 82, 100)}

    def text(self, text, size, color, center):
        surface = self.fonts[size].render(text, True, color)
        self.canvas.blit(surface, surface.get_rect(center=center))

    def draw(self, progress=None, status='', elapsed=0):
        self.canvas.blit(self.background, (0, 0))
        panel = pygame.Rect(356, 244, 1208, 665)
        pygame.draw.rect(self.canvas, (5, 19, 21), panel)
        # A quiet grid and drifting lights give the title a living forest feel.
        for x in range(panel.left, panel.right, 44):
            pygame.draw.line(self.canvas, (9, 31, 32), (x, panel.top), (x, panel.bottom))
        for y in range(panel.top, panel.bottom, 44):
            pygame.draw.line(self.canvas, (9, 31, 32), (panel.left, y), (panel.right, y))
        for i in range(23):
            x = panel.left + 24 + (i * 163 + math.sin(elapsed * .4 + i) * 22) % (panel.width - 48)
            y = panel.top + 20 + (i * 97 - elapsed * (6 + i % 4)) % (panel.height - 40)
            color = (42, 95 + int(35 * math.sin(elapsed + i)), 67)
            pygame.draw.circle(self.canvas, color, (round(x), round(y)), 2)
        self.text('A LITTLE WIZARD. A WORLD OF GAMES.', 22, (139, 193, 160), (960, 324))
        self.text('ARCADE', 100, (224, 249, 225), (960, 421))
        self.text('ODYSSEY', 82, (110, 240, 148), (960, 519))
        pygame.draw.line(self.canvas, (56, 111, 77), (812, 589), (1108, 589), 2)
        self.text('Explore the wild. Find your next high score.', 28, (168, 194, 181), (960, 633))
        if progress is not None:
            track = pygame.Rect(650, 733, 620, 7)
            pygame.draw.rect(self.canvas, (26, 55, 43), track, border_radius=3)
            fill = track.copy(); fill.width = round(track.width * max(0, min(1, progress)))
            if fill.width:
                pygame.draw.rect(self.canvas, (111, 238, 147), fill, border_radius=3)
            self.text(status, 22, (156, 190, 168), (960, 778))
        else:
            pulse = (math.sin(elapsed * 2.5) + 1) / 2
            button = pygame.Rect(748, 708, 424, 70)
            pygame.draw.rect(self.canvas, (21, 58, 39), button, border_radius=12)
            pygame.draw.rect(self.canvas, (74, round(160 + 70 * pulse), 112), button, 2, border_radius=12)
            self.text('ENTER  /  BEGIN ADVENTURE', 22, (225, 247, 225), button.center)
            self.text('A / D  Move     SPACE  Jump     ENTER  Play arcade', 18, (149, 180, 162), (960, 827))
            self.text('ESC  Quit', 18, (108, 145, 125), (960, 867))
        scaled = pygame.transform.smoothscale(self.canvas, self.screen.get_size())
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()
        pygame.event.pump()

    def show(self):
        clock = pygame.time.Clock()
        start = pygame.time.get_ticks()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        return True
            self.draw(elapsed=(pygame.time.get_ticks() - start) / 1000)
            clock.tick(60)
