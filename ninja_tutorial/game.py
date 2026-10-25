import math
from pathlib import Path
import random
import random
import sys
 
import pygame
from scripts.particles import Particles

from scripts.utilities import load_image, load_images ,Animations
from scripts.entities import PhysicsEntity , Player
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds

BASE_PATH = str(Path(__file__).parent.parent.resolve() / "ninja_tutorial")


class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('ninja game')
        self.screen = pygame.display.set_mode((640, 480) , pygame.SCALED)
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()
        
        self.movement = [False, False]
        
        self.assets = {
            'decor': load_images('/tiles/decor'),
            'grass': load_images('/tiles/grass'),
            'large_decor': load_images('/tiles/large_decor'),
            'stone': load_images('/tiles/stone'),
            'player': load_image('/entities/player.png'),
            "background": load_image('/background.png'),
            "clouds": load_images('/clouds'),
            "player_idle" : Animations(load_images('/entities/player/idle'), image_dur = 6),
            "player_run" : Animations(load_images('/entities/player/run'), image_dur = 4),
            "player_jump" : Animations(load_images('/entities/player/jump') ),
            "player_slide" : Animations(load_images('/entities/player/slide') ),
            "player_wall_slide" : Animations(load_images('/entities/player/wall_slide') ),
            "particles_leaf" : Animations(load_images('/particles/leaf'), image_dur = 20, loop = False),
            "particles_particle" : Animations(load_images('/particles/particle'), image_dur = 6, loop = False),
        }

        self.clouds = Clouds(self.assets["clouds"] , count = 16)
        
        self.player = Player(self, (50, 50), (8, 15))
        
        self.tilemap = Tilemap(self, tile_size=16)
        self.tilemap.load(f"{BASE_PATH}/tilemap.json")
        self.scroll = [0, 0]


        self.leaf_spawners  =[]

        for tree in self.tilemap.extract_tiles([("large_decor", 2)], keep = True):
            self.leaf_spawners.append(pygame.Rect(4+tree["pos"][0], 4+tree["pos"][1], 23, 18))

        self.particles = []

        
    def run(self):
        while True:
            self.display.blit(self.assets['background'], (0, 0))

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() // 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() // 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.clouds.update()
            self.clouds.render(self.display , offset=render_scroll)

            
            self.tilemap.render(self.display  , offset=render_scroll)


            for rect in self.leaf_spawners:
                if random.random() * 30000 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width , rect.y + random.random() * rect.height)
                    self.particles.append(Particles(self, "leaf", pos, velocity = [-0.2, 0.6 ] , frame = random.randint(0, 17)))

            
            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
            self.player.render(self.display , offset=render_scroll)


            for particle in self.particles.copy():
                particle.render(self.display , offset=render_scroll)
                kill = particle.update()
                if particle.type == "leaf":
                    particle.pos[0] +=math.sin(particle.animation.frame * 0.035) * 0.3
                if kill :
                    self.particles.remove(particle)

            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN :
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_w or event.key == pygame.K_SPACE:
                        self.player.jump()
                    if event.key == pygame.K_x:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
            
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Game().run()