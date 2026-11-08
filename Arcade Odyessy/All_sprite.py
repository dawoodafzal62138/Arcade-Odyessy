from settigns import *


class AllSprites(pygame.sprite.LayeredUpdates):
    def __init__(self):
        super().__init__()

        self.offset = pygame.Vector2()
        self.parallax_origin = None
        self.display_surface = pygame.display.get_surface()

    def draw(self, target_pos):
        if not self.display_surface:
            self.display_surface = pygame.display.get_surface()

        self.offset.x = target_pos[0] - WIDTH / 2
        self.offset.y = target_pos[1] - HEIGHT / 2

        # Anchor parallax to the initial view so distant map coordinates stay aligned.
        if self.parallax_origin is None:
            self.parallax_origin = self.offset.copy()

        # Frustum culling box (screen view + margin to avoid popping)
        screen_rect = pygame.Rect(
            self.offset.x - 256,
            self.offset.y - 256,
            WIDTH + 512,
            HEIGHT + 512
        )

        for sprite in self.sprites():
            sprite_rect = getattr(sprite, 'image_rect', sprite.rect)
            factor = getattr(sprite, 'parallax_factor', 1.0)
            draw_offset = self.offset
            view_rect = screen_rect
            if factor != 1.0:
                draw_offset = self.parallax_origin + (self.offset - self.parallax_origin) * factor
                view_rect = pygame.Rect(draw_offset.x - 256, draw_offset.y - 256,
                                        WIDTH + 512, HEIGHT + 512)
            if sprite_rect.colliderect(view_rect):
                draw_pos = sprite_rect.topleft - draw_offset
                self.display_surface.blit(sprite.image, draw_pos)
