from settigns import *


class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()

        self.offset = pygame.Vector2()
        self.display_surface = pygame.display.get_surface()

    def draw(self, target_pos):
        if not self.display_surface:
            self.display_surface = pygame.display.get_surface()

        self.offset.x = target_pos[0] - WIDTH / 2
        self.offset.y = target_pos[1] - HEIGHT / 2

        for sprite in self:
            draw_pos = getattr(sprite, 'image_rect', sprite.rect).topleft - self.offset
            self.display_surface.blit(sprite.image, draw_pos)
