"""Procedural scenery and restrained lighting for the overworld."""
import math
import random
import pygame
from sky import NightSky


class Atmosphere:
    def __init__(self, size, machines=(), platforms=()):
        self.width, self.height = size
        self.platforms = list(platforms)
        self.player = None
        self.eye_glow = self.make_glow(14, (255, 195, 95), 90)
        self.shadow = pygame.Surface((128, 32), pygame.SRCALPHA)
        for inset in range(12):
            pygame.draw.ellipse(self.shadow, (5, 12, 22, 2 + inset * 2),
                                (inset * 3, inset, 128 - inset * 6, 32 - inset * 2))
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
        self.machine_lights = []
        for color in ((75, 220, 115), (65, 195, 230)):
            # Additive light brightens existing grass texture rather than covering it.
            halo = self.make_light((360, 320), color, 0.09)
            ground = self.make_light((480, 140), color, 0.24)
            self.machine_lights.append((halo, ground))
        self.particle_glows = {
            'green': self.make_glow(12, (125, 255, 145), 85),
            'cyan': self.make_glow(12, (90, 235, 255), 85),
        }
        # World-space clusters stay attached to landmarks as the camera moves.
        self.particle_clusters = []
        for machine in machines:
            self.add_cluster(machine.rect.center, max(90, machine.rect.width), 105, 32)
        for platform in platforms:
            rect = platform.rect
            # Small, shallow collision surfaces identify the floating platforms.
            if 60 <= rect.width <= 360 and rect.height <= 100:
                self.add_cluster(rect.midtop, rect.width * 0.6, 65, 22)
        self.pollen = [(self.rng.random() * self.width,
                        self.rng.random() * self.height,
                        self.rng.uniform(0, math.tau)) for _ in range(42)]
        self.sky = NightSky(size)
        self.parallax_origin = None
        self.hills = []
        # Periodic silhouettes meet at tile boundaries, even on long traversals.
        for index, (depth, color) in enumerate((
                (0.05, (43, 70, 93, 75)),
                (0.08, (33, 61, 82, 85)),
                (0.16, (26, 67, 72, 110)),
                (0.26, (20, 53, 60, 135)))):
            period = self.width * 2
            surface = pygame.Surface((period, self.height), pygame.SRCALPHA)
            points = [(0, self.height)]
            for x in range(0, period + 1, 8):
                angle = x / period * math.tau
                y = self.height * (0.59 + depth)
                y += math.sin(angle * (3 + index) + index * 0.8) * self.height * 0.06
                y += math.sin(angle * (7 + index) + index) * self.height * 0.018
                points.append((x, round(y)))
            points.append((period, self.height))
            pygame.draw.polygon(surface, color, points)
            self.hills.append((depth, surface))
        self.mist_layers = []
        for index, (depth, wind, y, alpha) in enumerate((
                (0.38, 10, 0.72, 13), (0.62, -16, 0.83, 17),
                (0.88, 23, 0.93, 21))):
            surface = self.make_vapor(self.width * 2, max(40, round(self.height * 0.2)),
                                      (155, 205, 200), alpha, index + 3)
            self.mist_layers.append((depth, wind, y, surface))
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

    @staticmethod
    def make_vapor(width, height, color, alpha, phase):
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        # Nested translucent lobes give soft edges without per-frame blur work.
        for i in range(5):
            cx = (i + 0.5) * width / 5
            cy = height * (0.45 + math.sin(i * 2 + phase) * 0.12)
            for step in range(12):
                scale = 1 - step * 0.055
                rect = pygame.Rect(0, 0, round(width * 0.23 * scale),
                                   round(height * 0.9 * scale))
                rect.center = (round(cx), round(cy))
                pygame.draw.ellipse(surface, (*color, round(alpha * (step + 1) / 12)), rect)
        return surface

    def draw_repeating_layer(self, screen, surface, x, y):
        period = surface.get_width()
        start = round(x) % period - period
        for left in range(start, self.width, period):
            screen.blit(surface, (left, round(y)))

    def draw_vapor_layers(self, screen, layers, camera):
        for depth, wind, y, surface in layers:
            # Limit vertical travel to keep sky and ground layers in their bands.
            vertical = math.tanh(camera.y / max(1, self.height)) * self.height * depth * 0.12
            self.draw_repeating_layer(screen, surface,
                                      -camera.x * depth + self.time * wind,
                                      self.height * y - surface.get_height() / 2 - vertical)

    @staticmethod
    def make_light(size, color, strength):
        surface = pygame.Surface(size)
        width, height = size
        # Cache a smooth elliptical falloff; black edges add no light.
        for y in range(height):
            dy = (y - height / 2) / (height / 2)
            for x in range(width):
                dx = (x - width / 2) / (width / 2)
                falloff = max(0, 1 - dx * dx - dy * dy) ** 2 * strength
                if falloff:
                    surface.set_at((x, y), tuple(round(c * falloff) for c in color))
        return surface

    def draw_machine_lights(self, screen, offset, machines):
        view = screen.get_rect()
        for index, machine in enumerate(machines):
            halo, ground = self.machine_lights[index % len(self.machine_lights)]
            base = pygame.Vector2(machine.rect.midbottom) - offset
            ground_rect = ground.get_rect(center=(round(base.x), round(base.y + 5)))
            halo_rect = halo.get_rect(midbottom=(round(base.x), round(base.y + 30)))
            if view.colliderect(ground_rect) or view.colliderect(halo_rect):
                screen.blit(halo, halo_rect, special_flags=pygame.BLEND_RGB_ADD)
                screen.blit(ground, ground_rect, special_flags=pygame.BLEND_RGB_ADD)

    def add_cluster(self, center, spread, height, count):
        particles = []
        for i in range(count):
            kind = ('firefly', 'pollen', 'magic')[i % 3]
            particles.append((kind, self.rng.uniform(-spread, spread),
                              self.rng.uniform(0, height),
                              self.rng.uniform(0, math.tau),
                              self.rng.uniform(0.6, 1.3),
                              'green' if i % 2 else 'cyan'))
        self.particle_clusters.append((pygame.Vector2(center), spread, height, particles))

    def draw_particles(self, offset):
        colors = {'green': (145, 255, 165), 'cyan': (110, 240, 255)}
        for x, y, phase in self.pollen:
            px = (x + self.time * 9 - offset.x * 0.3 + math.sin(self.time * 0.4 + phase) * 16) % self.width
            py = (y + self.time * 4 - offset.y * 0.2 + math.cos(self.time * 0.3 + phase) * 12) % self.height
            pygame.draw.circle(self.overlay, (225, 240, 170, 85), (round(px), round(py)), 1)
        for anchor, spread, height, particles in self.particle_clusters:
            center = anchor - offset
            if not (-spread - 40 < center.x < self.width + spread + 40 and
                    -height - 50 < center.y < self.height + height + 50):
                continue
            for kind, x, y, phase, speed, color in particles:
                t = self.time * speed
                pulse = (math.sin(t * 1.8 + phase) + 1) * 0.5
                if kind == 'firefly':
                    px = center.x + x + math.sin(t * 0.7 + phase) * 22
                    py = center.y - y + math.cos(t * 0.6 + phase) * 16
                    glow = self.particle_glows[color]
                    glow.set_alpha(round(80 + 175 * pulse))
                    self.overlay.blit(glow, (round(px) - 12, round(py) - 12))
                    pygame.draw.circle(self.overlay, (*colors[color], round(95 + 160 * pulse)),
                                       (round(px), round(py)), 2)
                else:
                    progress = (y / height + t * (0.07 if kind == 'magic' else 0.025)) % 1
                    px = center.x + x + math.sin(t + phase) * 12
                    py = center.y + 20 - progress * height
                    alpha = round(170 * math.sin(math.pi * progress))
                    point = (round(px), round(py))
                    tint = colors[color] if kind == 'magic' else (225, 240, 170)
                    pygame.draw.circle(self.overlay, (*tint, alpha), point, 1)
                    if kind == 'magic' and pulse > 0.85:
                        pygame.draw.line(self.overlay, (*tint, alpha),
                                         (point[0] - 2, point[1]), (point[0] + 2, point[1]))
                        pygame.draw.line(self.overlay, (*tint, alpha),
                                         (point[0], point[1] - 2), (point[0], point[1] + 2))

    def update(self, dt, player):
        self.player = player
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
        if self.parallax_origin is None:
            self.parallax_origin = pygame.Vector2(offset)
        camera = offset - self.parallax_origin
        self.sky.draw_sky(screen, camera, self.time, self.draw_repeating_layer)
        for depth, surface in self.hills:
            self.draw_repeating_layer(screen, surface, -camera.x * depth, 0)
        self.sky.draw_forests(screen, camera, self.draw_repeating_layer)
        self.overlay.fill((0, 0, 0, 0))
        # One cool moonbeam occasionally fades in, with long quiet intervals.
        cycle = self.time % 26
        if 8 < cycle < 17:
            envelope = math.sin((cycle - 8) / 9 * math.pi) ** 2
            x = self.width * 0.38 - camera.x * 0.035
            x = x % (self.width + 500) - 250
            for feather in range(8):
                inset = feather * 7
                pygame.draw.polygon(self.overlay, (175, 205, 245, round(envelope * (2 + feather))),
                                    [(x + inset, 0), (x + 110 - inset, 0),
                                     (x + 480 - inset, self.height),
                                     (x + 190 + inset, self.height)])
        screen.blit(self.overlay, (0, 0))

    def draw_shadows(self, screen, offset):
        casters = [p for p in self.platforms
                   if 60 <= p.rect.width <= 360 and p.rect.height <= 100]
        if self.player:
            casters.append(self.player)
        for caster in casters:
            rect = caster.rect
            if not (-400 < rect.centerx - offset.x < self.width + 400 and
                    -500 < rect.bottom - offset.y < self.height + 100):
                continue
            supports = [p.rect.top for p in self.platforms if p is not caster
                        and p.rect.left <= rect.centerx <= p.rect.right
                        and rect.bottom - 6 <= p.rect.top <= rect.bottom + 500]
            if not supports:
                continue
            ground_y = min(supports)
            distance = max(0, ground_y - rect.bottom)
            scale = 1 - distance / 700
            width = max(16, round(min(240, rect.width * 0.8) * scale))
            shadow = pygame.transform.smoothscale(self.shadow, (width, max(5, round(22 * scale))))
            shadow.set_alpha(round(160 * (1 - distance / 550)))
            position = (round(rect.centerx - offset.x), round(ground_y - offset.y + 3))
            screen.blit(shadow, shadow.get_rect(center=position))

    def draw_eye_glow(self, screen, offset):
        if not self.player:
            return
        origin = pygame.Vector2(self.player.image_rect.topleft) - offset
        self.eye_glow.set_alpha(round(165 + 15 * math.sin(self.time * 1.5)))
        for point in getattr(self.player, 'eye_points', ()):
            position = origin + pygame.Vector2(point)
            screen.blit(self.eye_glow, (round(position.x) - 14, round(position.y) - 14))

    def draw_front(self, screen, offset, machines, active_machine):
        self.draw_shadows(screen, offset)
        self.draw_machine_lights(screen, offset, machines)
        self.draw_eye_glow(screen, offset)
        self.overlay.fill((0, 0, 0, 0))
        self.draw_particles(offset)
        # Windblown leaves nearer the camera.
        for i in range(10):
            x = int((i * 237 + self.time * 24 - offset.x * 0.65) % self.width)
            y = int((i * 139 + self.time * 13 + math.sin(self.time + i) * 20 - offset.y * 0.3) % self.height)
            pygame.draw.ellipse(self.overlay, (130, 175, 115, 100), (x, y, 7, 3))
        for position, velocity, life, duration in self.dust:
            point = position - offset
            pygame.draw.circle(self.overlay, (170, 215, 185, int(140 * life / duration)),
                               (round(point.x), round(point.y)), max(1, int(5 * life / duration)))
        for index, machine in enumerate(machines):
            center = pygame.Vector2(machine.rect.center) - offset
            if -250 < center.x < self.width + 250 and -250 < center.y < self.height + 250:
                tint = (120, 255, 165) if index % 2 == 0 else (120, 235, 255)
                # A gentle screen flicker rather than changing machine artwork.
                pygame.draw.line(self.overlay, (*tint, 90),
                                 (center.x - 12, center.y + math.sin(self.time * 3) * 9),
                                 (center.x + 12, center.y + math.sin(self.time * 3) * 9), 2)
        screen.blit(self.overlay, (0, 0))
        camera = offset - (self.parallax_origin if self.parallax_origin is not None else offset)
        self.draw_vapor_layers(screen, self.mist_layers, camera)
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
