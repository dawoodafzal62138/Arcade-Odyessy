"""Procedural scenery and restrained lighting for the overworld."""
import math
import random
import pygame


class Atmosphere:
    def __init__(self, size):
        self.width, self.height = size
        self.rng = random.Random(17)
        self.time = 0.0
        self.reveal = 0.0
        self.was_grounded = False
        self.dust = []
        self.font = pygame.font.Font(None, 30)
        self.title = pygame.font.Font(None, 68)
        self.overlay = pygame.Surface(size, pygame.SRCALPHA)
        self.black = pygame.Surface(size)
        self.black.fill('black')
        self.glow = self.make_glow(112, (105, 205, 160), 60)
        self.machine_glow = self.make_glow(220, (60, 200, 235), 75)
        self.fireflies = [(self.rng.random() * self.width,
                           self.rng.random() * self.height,
                           self.rng.uniform(0, math.tau)) for _ in range(38)]
        self.hills = []
        for depth, color in ((0.08, (33, 61, 82, 85)),
                             (0.16, (26, 67, 72, 110)),
                             (0.26, (20, 53, 60, 135))):
            surface = pygame.Surface((self.width * 2, self.height), pygame.SRCALPHA)
            points = [(0, self.height)]
            for x in range(0, self.width * 2 + 32, 32):
                y = self.height * (0.62 + depth) + math.sin(x / 220) * 65 + math.sin(x / 93) * 18
                points.append((x, int(y)))
            points.append((self.width * 2, self.height))
            pygame.draw.polygon(surface, color, points)
            self.hills.append((depth, surface))
        self.vignette = pygame.Surface(size, pygame.SRCALPHA)
        for i in range(30):
            pygame.draw.rect(self.vignette, (4, 12, 24, max(0, 35 - i)),
                             (i * 3, i * 2, self.width - i * 6, self.height - i * 4), 3)

    @staticmethod
    def make_glow(radius, color, alpha):
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for r in range(radius, 0, -4):
            strength = int(alpha * (1 - r / radius) ** 2)
            pygame.draw.circle(surface, (*color, strength), (radius, radius), r)
        return surface

    def update(self, dt, player):
        dt = min(dt, 0.05)
        self.time += dt
        self.reveal = min(1.0, self.reveal + dt / 1.4)
        if player:
            grounded = player.on_floor
            if grounded and not self.was_grounded:
                for _ in range(14):
                    self.dust.append([pygame.Vector2(player.rect.midbottom),
                                      pygame.Vector2(self.rng.uniform(-90, 90), self.rng.uniform(-65, -10)),
                                      0.55, 0.55])
            self.was_grounded = grounded
        for p in self.dust:
            p[0] += p[1] * dt
            p[2] -= dt
        self.dust = [p for p in self.dust if p[2] > 0][-100:]

    def draw_back(self, screen, offset):
        for depth, surface in self.hills:
            x = int(-offset.x * depth) % self.width
            screen.blit(surface, (x - self.width, 0))
        self.overlay.fill((0, 0, 0, 0))
        # Broad translucent shafts of sunlight.
        for i in range(3):
            x = int(self.width * (0.12 + i * 0.32) - offset.x * 0.035) % (self.width + 500) - 250
            pygame.draw.polygon(self.overlay, (255, 225, 175, 12),
                                [(x, 0), (x + 90, 0), (x + 490, self.height), (x + 210, self.height)])
        screen.blit(self.overlay, (0, 0))

    def draw_front(self, screen, offset, machines, active_machine):
        self.overlay.fill((0, 0, 0, 0))
        for x, y, phase in self.fireflies:
            px = (x - offset.x * 0.35 + math.sin(self.time * 0.5 + phase) * 38) % self.width
            py = (y - offset.y * 0.12 + math.cos(self.time * 0.4 + phase) * 26) % self.height
            pulse = (math.sin(self.time * 1.4 + phase) + 1) / 2
            if pulse > 0.35:
                self.overlay.blit(self.glow, (int(px) - 112, int(py) - 112))
                pygame.draw.circle(self.overlay, (205, 245, 160, int(100 + 140 * pulse)), (int(px), int(py)), 2)
        # Windblown leaves nearer the camera.
        for i in range(10):
            x = int((i * 237 + self.time * 24 - offset.x * 0.65) % self.width)
            y = int((i * 139 + self.time * 13 + math.sin(self.time + i) * 20 - offset.y * 0.3) % self.height)
            pygame.draw.ellipse(self.overlay, (130, 175, 115, 100), (x, y, 7, 3))
        for position, velocity, life, duration in self.dust:
            point = position - offset
            pygame.draw.circle(self.overlay, (170, 215, 185, int(140 * life / duration)),
                               (round(point.x), round(point.y)), max(1, int(5 * life / duration)))
        for machine in machines:
            center = pygame.Vector2(machine.rect.center) - offset
            if -250 < center.x < self.width + 250 and -250 < center.y < self.height + 250:
                self.overlay.blit(self.machine_glow, center - pygame.Vector2(220, 220))
                # A gentle screen flicker rather than changing machine artwork.
                pygame.draw.line(self.overlay, (120, 235, 255, 90),
                                 (center.x - 12, center.y + math.sin(self.time * 3) * 9),
                                 (center.x + 12, center.y + math.sin(self.time * 3) * 9), 2)
        # Thin moving mist bands soften the lower scenery without obscuring play.
        for i in range(3):
            x = int((self.time * (8 + i * 3) - offset.x * 0.08 + i * 620) % (self.width + 800)) - 800
            pygame.draw.ellipse(self.overlay, (155, 205, 200, 10),
                                (x, self.height * (0.72 + i * 0.08), 1100, 100))
        screen.blit(self.overlay, (0, 0))
        screen.blit(self.vignette, (0, 0))
        if active_machine:
            center = pygame.Vector2(active_machine.rect.midtop) - offset
            label = self.font.render('ENTER  ·  ' + str(getattr(active_machine, 'name', 'Play')).replace('_', ' ').title(), True, (225, 250, 240))
            rect = label.get_rect(midbottom=(center.x, center.y - 24))
            pygame.draw.rect(screen, (15, 35, 45), rect.inflate(28, 18), border_radius=10)
            pygame.draw.rect(screen, (95, 200, 180), rect.inflate(28, 18), 1, border_radius=10)
            screen.blit(label, rect)
        if self.time < 4:
            alpha = int(255 * min(1, self.time) * min(1, max(0, 4 - self.time)))
            label = self.title.render('ARCADE ODYSSEY', True, (225, 245, 235))
            label.set_alpha(alpha)
            screen.blit(label, label.get_rect(center=(self.width / 2, self.height * 0.19)))
        if self.reveal < 1:
            self.black.set_alpha(int(255 * (1 - self.reveal)))
            screen.blit(self.black, (0, 0))
