import pygame
from sys import exit
from random import randint, uniform
from pathlib import Path

Current_dir = Path(__file__).parent.resolve()

pygame.init()
WIDTH,HEIGHT =1280,720
Display_surface=pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Space Shooter")
Clock=pygame.time.Clock()
running=True
pygame.mouse.set_visible(False)
pygame.mouse.set_relative_mode(True)

# sprites
class player(pygame.sprite.Sprite):
    def __init__(self,groups):
        super().__init__(groups)
        self.image=pygame.image.load(f"{Current_dir}/images/player.png").convert_alpha()
        self.rect=self.image.get_frect(center=(WIDTH/2,HEIGHT/2))
        self.player_speed=300
        self.player_direction=pygame.math.Vector2()
        self.can_shoot=True
        self.can_laser_shoot_time=0
        self.cooldown_time=200

    def laser_timer(self):
        if not self.can_shoot:
            current_time=pygame.time.get_ticks()
            if current_time-self.can_laser_shoot_time>self.cooldown_time:
                self.can_shoot=True
    def movement(self,dt):
        # keyboard input
        # keys_hold=pygame.key.get_pressed()
        # self.player_direction.x=int(keys_hold[pygame.K_RIGHT])-int(keys_hold[pygame.K_LEFT])
        # self.player_direction.y=int(keys_hold[pygame.K_DOWN])-int(keys_hold[pygame.K_UP])
        # if self.player_direction:
        #     self.player_direction=self.player_direction.normalize()   
        # self.rect.center+=self.player_direction*self.player_speed * dt
        # mouse input
        
        self.rect.center=pygame.mouse.get_pos()
        # boundaries
        if self.rect.top<=20:
            self.rect.top=20
        if self.rect.bottom >= HEIGHT-20:
            self.rect.bottom=HEIGHT-20    
        if self.rect.right >= WIDTH-20:
            self.rect.right=WIDTH-20
        if self.rect.left<=20:
            self.rect.left=20    
        button_pressed=pygame.mouse.get_just_pressed()[0]
        # keys_pressed=pygame.key.get_just_pressed()
        if self.can_shoot:
            if button_pressed: 
                laser(laser_surface,self.rect.midtop,(all_sprite,laser_sprite))
                laser_sound.play()
                self.can_shoot=False
                self.can_laser_shoot_time=pygame.time.get_ticks()
        self.laser_timer()
    
    
    def update(self,dt):
        self.movement(dt)
class stars(pygame.sprite.Sprite):
    def __init__(self, groups,surf):
        super().__init__(groups)
        self.image=surf
        self.rect=self.image.get_frect(center=(randint(1,WIDTH),randint(1,HEIGHT)))
    
class laser(pygame.sprite.Sprite):
    def __init__(self, surf , pos, groups):
        super().__init__(groups)
        self.image=surf
        self.rect=self.image.get_frect(midbottom=pos)
        
    def movement(self,dt):
        self.rect.y-=400 * dt
        if self.rect.centery < -20:
            self.kill()


    def update(self ,dt):
        self.movement(dt)

class meteor(pygame.sprite.Sprite):
    def __init__(self,surf,pos, groups):
        super().__init__(groups)
        self.orignal_surface=surf
        self.image=surf
        self.rect=self.image.get_frect(center=pos)
        self.start_time=pygame.time.get_ticks()
        self.lifetime=3000
        self.direction=pygame.math.Vector2((uniform(-0.5 ,0.5),1))
        self.speed=400
        self.rotation_speed=randint(30,100)
        self.rotation_angle=0
        #rotate

    def update(self,dt):
        self.rotation_speed+=5*dt
        self.rect.center+=self.speed * self.direction* dt
        if pygame.time.get_ticks() - self.start_time > self.lifetime:
            self.kill()
        self.rotation_angle+=self.rotation_speed*dt    
        self.image=pygame.transform.rotozoom(self.orignal_surface,self.rotation_angle,1)
        self.rect=self.image.get_frect(center=self.rect.center)

class animated_explosion(pygame.sprite.Sprite):
    def __init__(self, frames , pos, groups):
        super().__init__(groups)
        self.frames=frames
        self.frame_index=0
        self.image=self.frames[self.frame_index]
        self.rect=self.image.get_frect(center=pos)

    def update(self, dt):
        self.frame_index+=20*dt
        if self.frame_index<len(self.frames):
            self.image=self.frames[int(self.frame_index)]
        else:    
            self.kill()

def collision():
    global running
    collision_sprites=pygame.sprite.spritecollide(player1,metero_sprite,True,pygame.sprite.collide_mask)
    if collision_sprites:
        running=False
    for laser in laser_sprite:
        collided_laser=pygame.sprite.spritecollide(laser,metero_sprite,True,pygame.sprite.collide_mask)
        if collided_laser:
            animated_explosion(frames,laser.rect.midtop,all_sprite)
            explosion_sound.play()
            laser.kill()

def display_score():
    current_time=pygame.time.get_ticks()//100
    font_surface=font.render(str(current_time),True,(240,240,240))
    font_rect=font_surface.get_frect(midbottom=(WIDTH/2,HEIGHT-50))
    Display_surface.blit(font_surface,font_rect)
    pygame.draw.rect(Display_surface,(240,240,240),font_rect.inflate(20,10).move(0,-7),5,8)

all_sprite=pygame.sprite.Group()
star_surface=pygame.image.load(f"{Current_dir}/images/star.png").convert_alpha()
for i in range(21):
    stars(all_sprite,star_surface) 
metero_sprite=pygame.sprite.Group()
laser_sprite=pygame.sprite.Group()
player1=player(all_sprite)


#imports
meteor_surface=pygame.image.load(f"{Current_dir}/images/meteor.png").convert_alpha()
laser_surface=pygame.image.load(f"{Current_dir}/images/laser.png").convert_alpha()
frames=[pygame.image.load(f"{Current_dir}/images/explosion/{i}.png").convert_alpha() for i in range (21)]
explosion_sound=pygame.mixer.Sound(f"{Current_dir}/audio/explosion.wav")
font=pygame.font.Font(f"{Current_dir}/images/Oxanium-Bold.ttf",40)
explosion_sound.set_volume(0.7)
laser_sound=pygame.mixer.Sound(f"{Current_dir}/audio/laser.wav")
laser_sound.set_volume(0.6)
game_music=pygame.mixer.Sound(f"{Current_dir}/audio/game_music.wav")
game_music.set_volume(0.4)
game_music.play(loops=-1)




# event timers ---> meteor 
meteor_timer=pygame.USEREVENT+1
pygame.time.set_timer(meteor_timer,500)

# Game loop
try:
    while running:
        dt=Clock.tick()/1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running=False
            if event.type == pygame.KEYDOWN:
                if event.key== pygame.K_ESCAPE:
                    running=False 

            if event.type == meteor_timer:
                x,y=randint(0,WIDTH), randint(-300,-100)
                meteors=meteor(meteor_surface,(x,y),(all_sprite,metero_sprite))
                    



        collision()
        Display_surface.fill("#3b2749")    
        all_sprite.update(dt)
        display_score()
        all_sprite.draw(Display_surface)
        pygame.display.update()

            

except Exception as e:
    print(f"Error: {e}")
pygame.quit()
exit()




