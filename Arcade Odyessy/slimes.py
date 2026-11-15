"""Small animated slime inhabitants placed on exposed hub terrain."""
import random
import pygame


class Slime(pygame.sprite.Sprite):
    def __init__(self, anchor, frames, group, variant, phase):
        super().__init__(group)
        self.anchor = anchor
        self.frames = frames
        self.variant = variant
        self.frame_index = phase
        self.image = frames[int(phase) % len(frames)]
        self.rect = self.image.get_rect(midbottom=anchor)

    def update(self, dt):
        self.frame_index = (self.frame_index + 12 * dt) % len(self.frames)
        self.image = self.frames[int(self.frame_index)]
        self.rect = self.image.get_rect(midbottom=self.anchor)


def load_slimes(directory):
    animations = []
    for variant in ('SlimeGreen', 'SlimeOrange'):
        paths = sorted((directory / variant).glob('*.png'))
        if not paths:
            continue
        images = [pygame.image.load(path).convert_alpha() for path in paths]
        bounds = [image.get_bounding_rect(min_alpha=32) for image in images]
        scale = 78 / max(1, max(rect.width for rect in bounds))
        frames = []
        for image, rect in zip(images, bounds):
            cropped = image.subsurface(rect)
            frames.append(pygame.transform.smoothscale(cropped,
                          (max(1, round(rect.width * scale)),
                           max(1, round(rect.height * scale)))))
        animations.append((variant, frames))
        pygame.event.pump()
    return animations


def add_slimes(tmx_map, group, machines, player, plants, directory, tile_scale, layer):
    animations = load_slimes(directory)
    if not animations:
        return []
    ground = tmx_map.get_layer_by_name('Ground')
    if not ground.visible:
        return []
    tiles = {(x, y): image for x, y, image in ground.tiles()}
    tile_w = tmx_map.tilewidth * tile_scale
    tile_h = tmx_map.tileheight * tile_scale
    rng = random.Random(83)
    # Visit regions in turn so scenery is spread across the entire map.
    regions = {}
    for x, y in sorted(tiles):
        if (x, y - 1) not in tiles:
            regions.setdefault(int(x * tile_w // 900), []).append((x, y))
    for candidates in regions.values():
        rng.shuffle(candidates)
    candidates = []
    while any(regions.values()):
        for region in sorted(regions):
            if regions[region]:
                candidates.append(regions[region].pop())
    if player:
        # Populate the starting route first, then expand into surrounding areas.
        spawn_x, spawn_y = player.rect.midbottom
        candidates.sort(key=lambda tile: (
            ((tile[0] + 0.5) * tile_w - spawn_x) ** 2
            + (tile[1] * tile_h - spawn_y) ** 2 * 2))
    slimes = []
    mask_cache = {}
    for x, y in candidates:
        variant, frames = animations[len(slimes) % len(animations)]
        width = max(frame.get_width() for frame in frames)
        height = max(frame.get_height() for frame in frames)
        if width + 20 > tile_w:
            continue
        image = tiles[x, y]
        if image not in mask_cache:
            mask_cache[image] = pygame.mask.from_surface(image, 32)
        mask = mask_cache[image]
        local_x = tile_w / 2
        support = []
        for dx in (-width / 2, 0, width / 2):
            column = min(image.get_width() - 1, max(0, round((local_x + dx) / tile_scale)))
            support.append(next((row for row in range(image.get_height())
                                 if mask.get_at((column, row))), None))
        if any(top is None for top in support):
            continue
        if (max(support) - min(support)) * tile_scale > 8:
            continue
        anchor = (round(x * tile_w + local_x), round(y * tile_h + support[1] * tile_scale + 12))
        area = pygame.Rect(0, 0, width, height)
        area.midbottom = anchor
        if any(area.colliderect(machine.rect.inflate(140, 60)) for machine in machines):
            continue
        if player and area.colliderect(player.rect.inflate(100, 40)):
            continue
        near_spawn = player and abs(anchor[0] - player.rect.centerx) < 900 and abs(anchor[1] - player.rect.bottom) < 450
        if not near_spawn and any(area.colliderect(plant.rect.inflate(20, 0)) for plant in plants):
            continue
        spacing = 110 if near_spawn else 180
        if any(abs(anchor[0] - other.anchor[0]) < spacing and
               abs(anchor[1] - other.anchor[1]) < 300 for other in slimes):
            continue
        slime = Slime(anchor, frames, group, variant, rng.randrange(len(frames)))
        group.change_layer(slime, layer - 0.1)
        slimes.append(slime)
        if len(slimes) >= 60:
            break
    return slimes
