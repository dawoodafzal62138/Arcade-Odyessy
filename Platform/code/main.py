from settings import * 
from sprite import *
from groups import *
from utils import *
from timer_ import Timer
import random

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT) , pygame.SCALED)
        pygame.display.set_caption('Platformer')
        self.clock = pygame.time.Clock()
        self.running = True

        # groups 
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()


        self.bee_timer= Timer(800 , func = self.create_bees , repeat = True , autostart = True)
        
        self.audios = {
            "impact": pygame.mixer.Sound(f"{CURRENT_PATH}/audio/impact.ogg"),
            "music": pygame.mixer.Sound(f"{CURRENT_PATH}/audio/music.wav"),
            "shoot": pygame.mixer.Sound(f"{CURRENT_PATH}/audio/shoot.wav")
        }
        


        #load game  
        self.load_asssets()
        self.setup()




    def create_bees(self):
        Bees(pos = (self.world_width  + 100,random.randint(0, self.world_height)) , 
             groups = (self.all_sprites , self.enemy_sprites) , 
             frames = self.bees_frames , 
             speed  = random.randint(300, 500))
    

    
    
    def create_bullet(self , pos , direction):
        x = pos[0] +  direction  * 34 if direction == 1 else pos[0] + direction  * 34 - self.bullet_surface.get_width()
        Bullet(pygame.transform.flip(self.bullet_surface, True, False) if direction == -1 else self.bullet_surface , (x , pos[1]) , direction , (self.all_sprites , self.bullet_sprites))
        Fire(self.fire_surface , pos , self.all_sprites , self.player)
        self.audios["shoot"].play()

    
    
    def load_asssets(self):

        self.player_frames = import_folder(f"{CURRENT_PATH}/images/player")
        self.bullet_surface = import_image(f"{CURRENT_PATH}/images/gun/bullet.png")
        self.fire_surface = import_image(f"{CURRENT_PATH}/images/gun/fire.png")

        self.bees_frames = import_folder(f"{CURRENT_PATH}/images/enemies/bee")
        self.worm_frames = import_folder(f"{CURRENT_PATH}/images/enemies/worm")
        
 


    def setup(self):
        tmx_map = load_pygame(f"{CURRENT_PATH}/data/maps/world.tmx")

        self.world_width = tmx_map.width * TILE_SIZE
        self.world_height = tmx_map.height * TILE_SIZE
        self.audios["music"].play(loops = -1).set_volume(0.3)

        for x, y , image in tmx_map.get_layer_by_name("Main").tiles():
            Sprite((x*TILE_SIZE, y*TILE_SIZE), image, (self.all_sprites , self.collision_sprites) )
        for x, y , image in tmx_map.get_layer_by_name("Decoration").tiles():
            Sprite((x*TILE_SIZE, y*TILE_SIZE), image, self.all_sprites )
        for obj in tmx_map.get_layer_by_name("Entities"):
            if obj.name == "Player":
                self.player = Player((obj.x, obj.y),  self.all_sprites , self.collision_sprites , self.player_frames , self.create_bullet)
            if obj.name == "Worm":
                self.worm =Worms(pygame.FRect(obj.x  , obj.y , obj.width, obj.height), (self.all_sprites , self.enemy_sprites) , self.worm_frames)
        
    def colllisions(self):
        for bullet_sprite in self.bullet_sprites:
            sprite_collisions = pygame.sprite.spritecollide(bullet_sprite , self.enemy_sprites , False , pygame.sprite.collide_mask)
            if sprite_collisions:
                bullet_sprite.kill()
                self.audios["impact"].play()
                for sprite in sprite_collisions:
                    sprite.destroy()
                    self.enemy_sprites.remove(sprite)

        if self.player.alive():
            if pygame.sprite.spritecollide(self.player , self.enemy_sprites , False , pygame.sprite.collide_mask):
                if not self.player.death_timer:
                    self.player.destroy()
        else:
            self.running = False

       
                    

    def run(self):
        while self.running:
            dt = self.clock.tick(FRAMERATE) / 1000 

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False 
            
            # update
            self.all_sprites.update(dt)
            self.colllisions()

            # draw 
            self.bee_timer.update()
            self.display_surface.fill(BG_COLOR)
            self.all_sprites.draw(self.player.rect.center)
            pygame.display.update()

        
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run() 