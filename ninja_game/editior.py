import sys
import pathlib
import pygame


from scripts.utilities import load_images
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds


BASE_PATH = str(pathlib.Path(__file__).parent.parent.resolve() / "ninja_game")



RENDER_SCALE = 2.0

class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Edition Mode')
        self.screen = pygame.display.set_mode((640, 480) , pygame.SCALED)
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()
        
        
        self.assets = {
            'grass': load_images('/tiles/grass'),
            'stone': load_images('/tiles/stone'),
            'decor': load_images('/tiles/decor'),
            'large_decor': load_images('/tiles/large_decor'),
            "spawner": load_images('/tiles/spawners'),
        
            
        }

        self.movement = [False, False , False , False]
        
        
        self.tilemap = Tilemap(self, tile_size=16)
        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.group = 0
        self.variant = 0
        self.left_cliking = False
        self.right_cliking = False
        self.shift_pressed = False
        self.ongrid = True

        try:
            self.tilemap.load(f"{BASE_PATH}/tilemap.json")
        except FileNotFoundError:
            print("No existing tilemap found. Starting with a new one.")


    def run(self):
        while True:
            self.display.fill((173, 216, 230))

            self.scroll[0] += (self.movement[1] - self.movement[0]) * 3
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 3
            
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display  , offset=render_scroll)
            
            current_image = self.assets[self.tile_list[self.group]][self.variant].copy()
            current_image.set_alpha(100)

            mouse_pos = pygame.mouse.get_pos()
            mouse_pos = (mouse_pos[0] //RENDER_SCALE , mouse_pos[1] // RENDER_SCALE)
            tile_pos = (int((mouse_pos[0]  + self.scroll[0]) // self.tilemap.tile_size) , int((mouse_pos[1]  + self.scroll[1]) // self.tilemap.tile_size))

            if self.left_cliking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ';' + str(tile_pos[1])] = {'type': self.tile_list[self.group], 'variant': self.variant, 'pos': tile_pos}

            if self.right_cliking:
                loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[loc]

                for tile in self.tilemap.offgrid_tiles:
                    tile_image = self.assets[tile["type"]][tile["variant"]]
                    t_r = pygame.Rect(tile["pos"][0]  - self.scroll[0] , tile["pos"][1] - self.scroll[1], tile_image.get_width(), tile_image.get_height())
                    if t_r.collidepoint(mouse_pos):
                        self.tilemap.offgrid_tiles.remove(tile)
                    

            
            self.display.blit(current_image, (5, 5))
            if self.ongrid:
                self.display.blit(current_image, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_image, mouse_pos)


            
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.left_cliking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append({'type': self.tile_list[self.group], 'variant': self.variant, 'pos': (mouse_pos[0] + self.scroll[0], mouse_pos[1] + self.scroll[1])})
                    
                    if self.shift_pressed:
                        if event.button == 4:
                            self.group  = (self.group - 1) % len(self.tile_list)
                            self.variant = 0
                        if event.button == 5:
                            self.group  = (self.group + 1) % len(self.tile_list)
                            self.variant = 0
                    else:
                        if event.button == 4:
                            self.variant  = (self.variant - 1) % len(self.assets[self.tile_list[self.group]])
                        if event.button == 5:
                            self.variant  = (self.variant + 1) % len(self.assets[self.tile_list[self.group]])

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.left_cliking = False
                  
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_o:
                        self.tilemap.save(f"{BASE_PATH}/tilemap.json")
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    
                    
                    
                    if event.key == pygame.K_LSHIFT:
                        self.shift_pressed = True
                    if event.key == pygame.K_LCTRL:
                        self.right_cliking = True

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift_pressed = False
                    if event.key == pygame.K_LCTRL:
                        self.right_cliking = False
                   
            
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)
Editor().run()