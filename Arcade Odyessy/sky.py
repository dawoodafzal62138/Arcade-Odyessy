"""Cached moonlit sky scenery; only small twinkles animate per frame."""
import math
import random
import pygame


class NightSky:
    def __init__(self, size):
        self.width, self.height = size
        rng = random.Random(109)
        self.stars = pygame.Surface((self.width * 2, round(self.height * 0.58)), pygame.SRCALPHA)
        self.twinkles = []
        for i in range(110):
            x = rng.randrange(self.stars.get_width())
            y = rng.randrange(self.stars.get_height())
            alpha = round(rng.randint(75, 155) * (1 - y / self.stars.get_height() * 0.75))
            pygame.draw.circle(self.stars, (185, 215, 235, alpha), (x, y), 1)
            if i % 9 == 0:
                self.twinkles.append((x, y, rng.random() * math.tau))
        radius = max(18, round(self.height * 0.052))
        self.moon = pygame.Surface((radius * 6, radius * 6), pygame.SRCALPHA)
        center = (radius * 3, radius * 3)
        for r in range(radius * 3, radius, -2):
            pygame.draw.circle(self.moon, (130, 185, 205, round(13 * (1 - r / (radius * 3)) ** 2)), center, r)
        disc = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(disc, (201, 220, 215, 225), (radius + 1, radius + 1), radius)
        pygame.draw.circle(disc, (0, 0, 0, 0), (round(radius * 1.5), round(radius * 0.72)), radius)
        self.moon.blit(disc, (radius * 2 - 1, radius * 2 - 1))
        self.auroras = []
        for index, color in enumerate(((70, 205, 159), (83, 151, 210))):
            # Build at quarter resolution once, then soften by upscaling.
            w, h = max(1, self.width // 2), max(1, self.height // 10)
            ribbon = pygame.Surface((w, h), pygame.SRCALPHA)
            for x in range(w):
                angle = x / w * math.tau
                crest = h * (0.44 + math.sin(angle * 2 + index) * 0.12 + math.sin(angle * 3) * 0.07)
                taper = math.sin(math.pi * x / w) ** 2
                for y in range(h):
                    distance = abs(y - crest) / max(1, h * 0.26)
                    alpha = round(24 * max(0, 1 - distance) ** 2 * taper)
                    if alpha:
                        ribbon.set_at((x, y), (*color, alpha))
            self.auroras.append(pygame.transform.smoothscale(ribbon, (self.width * 2, round(self.height * 0.4))))
        self.forests = []
        for index, (depth, tint) in enumerate(((0.11, (26, 58, 67, 125)), (0.20, (17, 45, 50, 165)))):
            w, h = self.width, max(1, round(self.height * 0.23))
            forest = pygame.Surface((w, h), pygame.SRCALPHA)
            def ground_y(x):
                angle = x / w * math.tau
                return h * (0.86 + math.sin(angle * 2) * 0.035
                            + math.sin(angle * 5 + index) * 0.018)

            points = [(0, h)] + [(x, round(ground_y(x)))
                      for x in range(0, w + 1, 4)] + [(w, h)]
            pygame.draw.polygon(forest, tint, points)
            x = rng.uniform(16, 30)
            while x < w - 20:
                # Loose groups separated by clearings, rather than a solid wall.
                cluster_size = rng.randint(2, 4)
                for _ in range(cluster_size):
                    if x >= w - 20:
                        break
                    base = ground_y(x) + 2
                    height = rng.uniform(h * 0.20, h * 0.48)
                    spread = height * rng.uniform(0.16, 0.25)
                    lean = rng.uniform(-0.06, 0.06) * height
                    trunk = max(1, round(height * 0.045))
                    pygame.draw.line(forest, tint, (round(x), round(base)),
                                     (round(x + lean), round(base - height)), trunk)
                    if rng.random() < 0.8:
                        # Asymmetric boughs taper towards a softly irregular tip.
                        left, right = [], []
                        for branch in range(7):
                            fraction = branch / 6
                            cy = base - height + fraction * height * 0.82
                            cx = x + lean * (1 - fraction)
                            extent = spread * fraction ** 0.8
                            left.append((cx - extent * rng.uniform(0.8, 1.15), cy))
                            left.append((cx - extent * 0.6, cy + height * 0.045))
                            right.append((cx + extent * rng.uniform(0.8, 1.15), cy))
                            right.append((cx + extent * 0.6, cy + height * 0.045))
                        pygame.draw.polygon(forest, tint, left + list(reversed(right)))
                    else:
                        # A few broadleaf crowns break up the conifer rhythm.
                        for crown in range(5):
                            cx = x + lean + rng.uniform(-spread, spread)
                            cy = base - height * rng.uniform(0.62, 0.85)
                            radius = max(2, round(height * rng.uniform(0.16, 0.24)))
                            pygame.draw.circle(forest, tint, (round(cx), round(cy)), radius)
                    x += rng.uniform(15, 28)
                x += rng.uniform(45, 95)
            self.forests.append((depth, pygame.transform.smoothscale(forest, (w * 2, h * 2))))
        self.twinkle_surface = pygame.Surface(size, pygame.SRCALPHA)

    def draw_sky(self, screen, camera, time, repeat):
        repeat(screen, self.stars, -camera.x * 0.012, 0)
        self.twinkle_surface.fill((0, 0, 0, 0))
        for x, y, phase in self.twinkles:
            px = round((x - camera.x * 0.012) % self.stars.get_width())
            pulse = max(0, math.sin(time * 0.65 + phase)) ** 6
            if px < self.width and pulse > 0.3:
                alpha = round(115 * pulse)
                pygame.draw.line(self.twinkle_surface, (195, 225, 240, alpha), (px - 2, y), (px + 2, y))
                pygame.draw.line(self.twinkle_surface, (195, 225, 240, alpha), (px, y - 2), (px, y + 2))
        screen.blit(self.twinkle_surface, (0, 0))
        for index, ribbon in enumerate(self.auroras):
            repeat(screen, ribbon, -camera.x * 0.018 + math.sin(time * 0.04 + index) * 45,
                   self.height * (0.07 + index * 0.10) + math.sin(time * 0.08 + index) * 8)
        moon_x = self.width * 0.76 - math.tanh(camera.x / (self.width * 4)) * self.width * 0.12
        moon_y = self.height * 0.62 - math.tanh(camera.y / self.height) * self.height * 0.02
        screen.blit(self.moon, self.moon.get_rect(center=(round(moon_x), round(moon_y))))

    def draw_forests(self, screen, camera, repeat):
        for index, (depth, forest) in enumerate(self.forests):
            repeat(screen, forest, -camera.x * depth, self.height * (0.44 + index * 0.12))
