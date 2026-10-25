from settings import *
from player import Player
from sprites import *
from groups import *




class Game:
    def __init__(self):
        
        pygame.init()
        self.display_surface=pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.mouse.set_visible(False) 
        pygame.mouse.set_relative_mode(True)
        pygame.display.set_caption("Vampire Shooter")
        self.Clock=pygame.time.Clock()
        self.running=True
        self.can_shoot=True
        self.shoot_cooldown=100
        self.spawn_pos=[]

        # audio
        self.shoot_sound=pygame.mixer.Sound(join("audio","shoot.wav"))
        self.shoot_sound.set_volume(0.3)
        self.music=pygame.mixer.Sound(join("audio","music.wav"))
        self.music.set_volume(0.2)
        self.impact_sound=pygame.mixer.Sound(join("audio","impact.ogg"))
        self.impact_sound.set_volume(0.5)
        self.music.play(loops=-1)

        # Groups
        self.all_sprites=AllSprites()
        self.collision_sprites=pygame.sprite.Group()
        self.bullet_sprite=pygame.sprite.Group()
        self.enemy_sprite=pygame.sprite.Group()
        self.crosshair_sprite=pygame.sprite.Group()
        


        # enemy_event
        self.enemy_event=pygame.USEREVENT+1
        pygame.time.set_timer(self.enemy_event,800)
        
        
        # setup
        self.setup()
        self.load_images()



        cursor(self.cursor_image,self.crosshair_sprite)

    def load_images(self):
        self.bullet_surface=pygame.image.load(join("images","gun","bullet.png")).convert_alpha()
        folders=list(walk(join("images","enemies")))[0][1] #this line will get the folder names in the path: images/enemies/
        self.enemy_frames={}
        for folder in folders:# we loop through every folder
        
            for folder_path ,sub_folder,file_names in walk(join("images","enemies",folder)):# get the folderpath and file name on the foder we loop through
                    self.enemy_frames[folder]=[]
                    for file_name in sorted(file_names,key=lambda name:int(name.split(".")[0])):
                        full_path=join(folder_path,file_name)
                        surface=pygame.image.load(full_path).convert_alpha()
                        self.enemy_frames[folder].append(surface)

        self.cursor_image=pygame.image.load(join("images","crossshair.png")).convert_alpha()
        self.cursor_image=pygame.transform.scale(self.cursor_image,(70,70))

    def shoot_timing(self):
        if not self.can_shoot:
            current_time=pygame.time.get_ticks()
            if current_time-self.shoot_time>self.shoot_cooldown:
                self.can_shoot=True




    def input(self):
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            pos=self.gun.rect.center+self.gun.player_direction*50
            bullet(self.bullet_surface,pos,self.gun.player_direction,(self.all_sprites,self.bullet_sprite))
            self.shoot_sound.play()
            self.shoot_time=pygame.time.get_ticks()
            self.can_shoot=False 
        self.shoot_timing()


    def collisions(self):
        if self.bullet_sprite:
            for bullet in self.bullet_sprite:
                collision_sprite=pygame.sprite.spritecollide(bullet,self.enemy_sprite,False,pygame.sprite.collide_mask)
                if collision_sprite:
                    self.impact_sound.play()
                    for sprite in collision_sprite:
                        sprite.destroy()
                    bullet.kill()

    def player_collision(self):
        if pygame.sprite.spritecollide(self.player,self.enemy_sprite,False,pygame.sprite.collide_mask):
            self.running=False
    def setup(self):
        map=load_pygame(join("data","maps","world.tmx"))

        for x,y,image in map.get_layer_by_name("Ground").tiles():
            Sprite(image,(x*TILE_SIZE,y*TILE_SIZE),self.all_sprites)
        for obj in map.get_layer_by_name("Objects"):
            CollisionSprites(obj.image,(obj.x,obj.y),(self.all_sprites,self.collision_sprites))
        for obj in map.get_layer_by_name("Collisions"):
            CollisionSprites(pygame.Surface((int(obj.width), int(obj.height))), (obj.x, obj.y), self.collision_sprites)
        for obj in map.get_layer_by_name("Entities"):
            if obj.name=="Player":
                self.player=Player( (obj.x,obj.y) ,self.all_sprites,self.collision_sprites)
                self.gun=Gun(self.player,self.all_sprites)
            else:
                self.spawn_pos.append((obj.x,obj.y))

    def health(self):
        rect=pygame.surface.Surface((50,50))
        rect.fill("black")
        self.display_surface.blit(rect,(WIDTH /6,HEIGHT/6))            

    def run(self):

        while self.running:
            
            
            # dt
            dt=self.Clock.tick(60)/1000
            # event loop
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    self.running=False
                if event.type==pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running=False    

                if event.type==self.enemy_event:
                    enemy(choice(list(self.enemy_frames.values())),choice(self.spawn_pos),self.player,self.collision_sprites,(self.all_sprites,self.enemy_sprite))
            self.input()
            # update
            self.all_sprites.update(dt)
            self.crosshair_sprite.update(dt)
            self.collisions()
            # self.player_collision()
            

            # draw
            self.display_surface.fill("black")
            self.all_sprites.draw(self.player.rect.center)
            self.crosshair_sprite.draw(self.display_surface)
            # self.health()
            pygame.display.update()          
        pygame.quit()
        exit()



if __name__=="__main__":
    game=Game()
    game.run()