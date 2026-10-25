from math import atan2 ,degrees
from settings import *


class Sprite(pygame.sprite.Sprite):
        def __init__(self,surf,pos, groups):
            super().__init__(groups)
            self.image=surf
            self.rect=self.image.get_frect(topleft=pos)
            self.ground=True


class CollisionSprites(pygame.sprite.Sprite):
    def __init__(self,surf,pos, groups):
        super().__init__(groups)
        self.image=surf
        self.rect=self.image.get_frect(topleft=pos)


class Gun(pygame.sprite.Sprite):

    def __init__(self,player, groups):
        #Player connection
        self.player=player
        self.distance=140
        self.player_direction=pygame.math.Vector2(0,1)

        super().__init__(groups)
        self.surf=pygame.image.load(join("images","gun","gun.png")).convert_alpha()
        self.image=self.surf
        self.rect=self.image.get_frect(center=self.player.rect.center+self.player_direction*self.distance)

    def rotation(self):
        angle=degrees(atan2(self.player_direction.x,self.player_direction.y))-90
        if self.player_direction.x>0:
            self.image=pygame.transform.rotozoom(self.surf,angle,1)
        else:
            self.image=pygame.transform.rotozoom(self.surf,abs(angle) ,1)
            self.image=pygame.transform.flip(self.image,False,True)
    
    
    def get_direction(self):
         try:
            mouse_pos=pygame.math.Vector2(pygame.mouse.get_pos())
            player_pos=pygame.math.Vector2((WIDTH/2,HEIGHT/2))
    
            if self.player_direction.length()>0:
                self.player_direction=(mouse_pos-player_pos).normalize()
            else:
                self.player_direction=(mouse_pos-player_pos)
         except Exception as e:
             pass    
    def update(self,dt):
        self.get_direction()
        self.rotation()
        self.rect.center=self.player.rect.center+self.player_direction*self.distance
    

class bullet(pygame.sprite.Sprite):
    def __init__(self, surf,pos,direction,groups):
        super().__init__(*groups)
        self.image=surf
        self.rect=self.image.get_frect(center=pos)
        self.speed=1200
        self.direction=direction
        self.time=pygame.time.get_ticks()
        self.life_time=1000


    def update(self,dt):
        self.rect.center+=self.speed *self.direction * dt    
        if pygame.time.get_ticks()-self.time > self.life_time:
            self.kill()


class enemy(pygame.sprite.Sprite):

    def __init__(self, frames,pos,player,collision_sprites,groups):
        super().__init__(*groups)
        self.player=player
        
        # images
        self.frames , self.frame_index=frames,0
        self.image=self.frames[self.frame_index]
        self.direction=pygame.math.Vector2()
        self.animation_speed=6

        # rects
        self.rect=self.image.get_frect(center=pos)
        self.hit_box=self.rect.inflate(-20,40)

        self.speed=300
        self.collision_sprites=collision_sprites
        self.death_time=0
        self.death_duration=400
    
    def animate(self,dt):
        self.frame_index+=self.animation_speed*dt
        self.image=self.frames[int(self.frame_index)%len(self.frames)]
    
    def move(self,dt):
        player_pos=pygame.math.Vector2(self.player.rect.center)
        enemy_pos=pygame.math.Vector2(self.rect.center)
        self.direction=(player_pos-enemy_pos).normalize()


        self.hit_box.x+=self.direction.x*self.speed*dt
        self.collisions("horizontal") 
        self.hit_box.y+=self.direction.y*self.speed*dt 
        self.collisions("vertical") 
        self.rect.center=self.hit_box.center
        
    def collisions(self,diretion):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hit_box):
                if diretion == "horizontal":
                    if self.direction.x > 0: self.hit_box.right=sprite.rect.left
                    if self.direction.x < 0: self.hit_box.left=sprite.rect.right
                else:
                    if self.direction.y > 0: self.hit_box.bottom=sprite.rect.top
                    if self.direction.y < 0: self.hit_box.top=sprite.rect.bottom

    
    def destroy(self):
        # change image
        surf=pygame.mask.from_surface(self.frames[0]).to_surface()
        surf.set_colorkey("black")
        self.image=surf

        self.death_time=pygame.time.get_ticks()
    
    def death_timer(self):
        if pygame.time.get_ticks()-self.death_time>self.death_duration:
            self.kill()
    
    def update(self,dt):
        if self.death_time==0:
            self.move(dt)
            self.animate(dt) 
        else:
            self.death_timer()  


class cursor(pygame.sprite.Sprite):
    def __init__(self,surf, groups):
        super().__init__(groups)
        self.image=surf
        self.rect=self.image.get_frect()                

    def update(self,dt):
        mouse_pos=pygame.mouse.get_pos() 
        self.rect.center=mouse_pos   