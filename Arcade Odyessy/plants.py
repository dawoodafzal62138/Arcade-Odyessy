"""Animated scenery rooted on exposed tiles of the overworld Ground layer."""
import math
import random
import pygame


class GroundPlant(pygame.sprite.Sprite):
    def __init__(self, anchor, frames, group, phase=0):
        super().__init__(group)
        self.frames = frames
        self.anchor = anchor
        self.sway_time = phase
        self.frame_index = phase
        self.image = frames[int(phase) % len(frames)]
        self.rect = self.image.get_rect(midbottom=anchor)

    def update(self, dt):
        self.frame_index = (self.frame_index + 24 * dt) % len(self.frames)
        self.sway_time += dt
        frame = self.frames[int(self.frame_index)]
        angle = math.sin(self.sway_time * 0.65 + self.anchor[0] * 0.013) * 2.0
        self.image = pygame.transform.rotate(frame, angle)
        # Rotate around the roots so stems remain planted.
        root = pygame.Vector2(0, frame.get_height() / 2).rotate(-angle)
        center = pygame.Vector2(self.anchor) - root
        self.rect = self.image.get_rect(center=(round(center.x), round(center.y)))


def load_plants(directory):
    animations = []
    for folder in sorted(directory.iterdir()):
        paths = sorted(folder.glob('*.png')) if folder.is_dir() else []
        if not paths:
            continue
        frames = []
        images = [pygame.image.load(path).convert_alpha() for path in paths]
        widest = max(image.get_bounding_rect(min_alpha=32).width for image in images)
        scale = min(0.25, 96 / max(1, widest))
        for image in images:
            # Remove export padding and pin the visible roots in every frame.
            bounds = image.get_bounding_rect(min_alpha=32)
            if not bounds.width or not bounds.height:
                continue
            image = image.subsurface(bounds)
            frames.append(pygame.transform.smoothscale(image,
                          (max(1, round(bounds.width * scale)),
                           max(1, round(bounds.height * scale)))))
        if frames:
            animations.append(frames)
        pygame.event.pump()
    return animations


def add_ground_plants(tmx_map, group, machines, player, directory, tile_scale, layer):
    animations = load_plants(directory)
    if not animations:
        return []
    ground = tmx_map.get_layer_by_name('Ground')
    if not ground.visible:
        return []
    tiles = {(x, y): image for x, y, image in ground.tiles()}
    tile_w = tmx_map.tilewidth * tile_scale
    tile_h = tmx_map.tileheight * tile_scale
    rng = random.Random(41)
    plants = []
    occupied = []
    for (x, y), image in sorted(tiles.items(), key=lambda item: (item[0][1], item[0][0])):
        if (x, y - 1) in tiles or rng.random() > 0.38:
            continue
        frames = animations[len(plants) % len(animations)]
        width = max(frame.get_width() for frame in frames)
        # Keep the entire root footprint supported by this tile.
        if width > tile_w - 16:
            continue
        local_x = rng.randint(round(width / 2 + 8), round(tile_w - width / 2 - 8))
        mask = pygame.mask.from_surface(image, 32)
        source_x = min(image.get_width() - 1, round(local_x / tile_scale))
        surface_y = next((row for row in range(image.get_height())
                          if mask.get_at((source_x, row))), None)
        if surface_y is None:
            continue
        anchor = (round(x * tile_w + local_x), round(y * tile_h + surface_y * tile_scale + 4))
        area = pygame.Rect(0, 0, width, max(frame.get_height() for frame in frames))
        area.midbottom = anchor
        if any(area.colliderect(machine.rect.inflate(100, 40)) for machine in machines):
            continue
        if player and area.colliderect(player.rect.inflate(160, 40)):
            continue
        if any(area.colliderect(other.inflate(60, 0)) for other in occupied):
            continue
        # Reject roots over a cliff or gap, checking support across their width.
        support = []
        for dx in (-width // 2, 0, width // 2):
            column = max(0, min(image.get_width() - 1, round((local_x + dx) / tile_scale)))
            top = next((row for row in range(image.get_height()) if mask.get_at((column, row))), None)
            support.append(top)
        if any(top is None or abs(top - surface_y) * tile_scale > 10 for top in support):
            continue
        plant = GroundPlant(anchor, frames, group, rng.randrange(len(frames)))
        group.change_layer(plant, layer - 0.1)
        plants.append(plant)
        occupied.append(area)
    return plants
