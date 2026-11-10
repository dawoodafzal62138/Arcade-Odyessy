"""Temporary control cards drawn on the cabinet, outside the game screen."""
import pygame
from settigns import CURRENT_DIR
from arcade_screen import cabinet

CONTROLS = {
    'flappy_bird': [(('Spacebar',), 'Flap / Play')],
    'ninja': [(('A', 'D'), 'Move'), (('Spacebar',), 'Jump'), (('X',), 'Dash')],
    'platform': [(('A', 'D'), 'Move'), (('W',), 'Jump'), (('Spacebar',), 'Shoot')],
    'tiny_titan': [(('A', 'D'), 'Move'), (('Spacebar',), 'Double jump')],
    'pixel_runner': [(('Spacebar',), 'Jump / Play'), (('S',), 'Slide')],
    'pong': [(('UpArrow', 'DownArrow'), 'Move'), (('R',), 'Reset')],
    'space_shooter': [(('W', 'A', 'S', 'D'), 'Move'), (('Spacebar',), 'Shoot'), ((), 'Mouse: Move / Fire')],
    'vampire_survivor': [(('W', 'A', 'S', 'D'), 'Move'), ((), 'Mouse: Aim / Fire')],
}


class ControlHints:
    def __init__(self, game):
        self.started = pygame.time.get_ticks()
        self.first_draw = True
        self.controls = CONTROLS[game] + [(('Escape',), 'Exit')]
        self.cards = {}

    def alpha(self, now):
        # Hold for five seconds, then fade smoothly over three seconds.
        return round(255 * max(0, min(1, (8000 - (now - self.started)) / 3000)))

    def card(self, size):
        if size in self.cards:
            return self.cards[size]
        font = pygame.font.Font(None, 25)
        pieces = []
        for keys, label in self.controls:
            for key in keys:
                image = pygame.image.load(CURRENT_DIR / 'resources' / 'Input UI V1' / (key + '.png')).convert_alpha()
                image = pygame.transform.smoothscale(image, (42, 42))
                pieces.append(image)
            pieces.append(font.render(label, True, (230, 245, 235)))
            pieces.append(pygame.Surface((18, 1), pygame.SRCALPHA))
        width = sum(piece.get_width() + 5 for piece in pieces) + 20
        card = pygame.Surface((width, 62), pygame.SRCALPHA)
        pygame.draw.rect(card, (8, 22, 23, 225), card.get_rect(), border_radius=12)
        pygame.draw.rect(card, (95, 165, 130, 230), card.get_rect(), 1, border_radius=12)
        x = 12
        for piece in pieces:
            card.blit(piece, (x, (62 - piece.get_height()) // 2))
            x += piece.get_width() + 5
        glass = cabinet(pygame.Surface(size)).glass
        available_height = max(1, size[1] - glass.bottom - 12)
        factor = min(1, (size[0] - 24) / width, available_height / 62)
        card = pygame.transform.smoothscale(card, (max(1, round(width * factor)), max(1, round(62 * factor))))
        self.cards[size] = card
        return card

    def draw(self, screen):
        if self.first_draw:
            self.started = pygame.time.get_ticks()
            self.first_draw = False
        alpha = self.alpha(pygame.time.get_ticks())
        if not alpha:
            return
        card = self.card(screen.get_size())
        card.set_alpha(alpha)
        glass = cabinet(screen).glass
        rect = card.get_rect(center=(screen.get_width() // 2, (glass.bottom + screen.get_height()) // 2))
        screen.blit(card, rect)
