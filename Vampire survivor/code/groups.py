from settings import *

class AllSprites(pygame.sprite.Group):
    def __init__(self ):
        super().__init__()
        self.display_surface=pygame.display.get_surface()
        self.offset=pygame.math.Vector2(100,100)

    def draw(self,target_pos, surface=None):
        draw_surf = surface if surface is not None else self.display_surface
        ground_sprite=[sprite for sprite in self if hasattr(sprite,"ground")]
        object_sprite=[sprite for sprite in self if not hasattr(sprite,"ground")]
        # this is the basic player camera
        self.offset.x=-(target_pos[0] - WIDTH/2)
        self.offset.y=-(target_pos[1] - HEIGHT/2)
        for layer in [ground_sprite,object_sprite]:
            for sprite in sorted(layer, key=lambda sprite: sprite.rect.centery):
                draw_surf.blit(sprite.image,sprite.rect.topleft+self.offset)