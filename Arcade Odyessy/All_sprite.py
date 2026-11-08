from settigns import *


class AllSprites(pygame.sprite.LayeredUpdates):
    def __init__(self):
        super().__init__()

        self.offset = pygame.Vector2()
        self.display_surface = pygame.display.get_surface()

    def draw(self, target_pos):
        if not self.display_surface:
            self.display_surface = pygame.display.get_surface()

        self.offset.x = target_pos[0] - WIDTH / 2
        self.offset.y = target_pos[1] - HEIGHT / 2

        # Frustum culling box (screen view + margin to avoid popping)
        screen_rect = pygame.Rect(
            self.offset.x - 256,
            self.offset.y - 256,
            WIDTH + 512,
            HEIGHT + 512
        )

        for sprite in self.sprites():
            sprite_rect = getattr(sprite, 'image_rect', sprite.rect)
            if sprite_rect.colliderect(screen_rect):
                draw_pos = sprite_rect.topleft - self.offset
                self.display_surface.blit(sprite.image, draw_pos)
