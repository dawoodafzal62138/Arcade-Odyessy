
import random

from settings import *
from timer_ import Timer
import math


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos , surface , groups):
        super().__init__(groups)
        self.image = surface
        self.rect = self.image.get_frect(topleft = pos)

class Animation(Sprite):
    def __init__(self, pos , frames , groups):
        self.frames = frames
        self.frame_index = 0
        self.animation_speed = 10
        super().__init__(pos , frames[self.frame_index] , groups)




    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image= self.frames[int(self.frame_index) % len(self.frames)]

class Bullet(Sprite):
    def __init__(self, surf , pos , direction , groups):
        super().__init__(pos , surf , groups)
        self.direction = direction
        self.speed = 850


    def update(self , dt):
        self.rect.x += self.direction * self.speed * dt

class Fire(Sprite):
    def __init__(self, surf , pos , groups, player):
        super().__init__(pos , surf , groups)
        self.player = player
        self.flip = self.player.flip
        self.timer = Timer(100 , autostart = True , func = self.kill)
        self.y_offset = pygame.Vector2(0 , 8)

        if self.flip:
            self.rect.midright = self.player.rect.midleft + self.y_offset
            self.image = pygame.transform.flip(self.image, True, False)
        else:
            self.rect.midleft = self.player.rect.midright + self.y_offset


    def update(self , _):
        self.timer.update()

        if self.flip:
            self.rect.midright = self.player.rect.midleft + self.y_offset
        else:
            self.rect.midleft = self.player.rect.midright + self.y_offset

        if self.flip != self.player.flip:
            self.kill()


class Player(Animation):
    def __init__(self, pos , groups , collisions_sprites , frames , create_bullet_func):
        super().__init__(pos , frames , groups)
        
        self.collisions_sprites = collisions_sprites
        self.create_bullet = create_bullet_func


        # movent and collisions
        self.direction = pygame.Vector2()
        self.speed = 400
        self.gravity = 50
        self.on_floor = False
        self.flip = False

        # timer
        self.timer = Timer(500)
        self.death_timer = Timer(1000 , func = self.kill)
    
    def destroy(self):
            self.death_timer.activate()
            self.animation_speed = 0
            self.image = pygame.mask.from_surface(self.image).to_surface()
            self.image.set_colorkey("black")
            

    def input(self ):
        key = pygame.key.get_pressed()
        self.direction.x = int(key[pygame.K_d]) - int(key[pygame.K_a]) or int(key[pygame.K_RIGHT]) - int(key[pygame.K_LEFT])
        if (key[pygame.K_w] or key[pygame.K_UP] )  and self.on_floor:
            self.direction.y = -20 
        
        
        if key[pygame.K_SPACE]  and not self.timer.active:
            self.create_bullet(self.rect.center , 1 if not  self.flip else -1 )
            
            self.timer.activate()
 
    def move(self, dt):
        self.rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')


        self.direction.y += self.gravity * dt
        self.rect.y += self.direction.y 
        self.collision('vertical')


    def update(self, dt):
        self.check_on_floor()
        self.timer.update()
        self.death_timer.update()
        if not self.death_timer:
            self.input()
            self.move(dt)
            self.animate(dt)

    def animate(self, dt):
        if self.direction.x == 0:
            self.frame_index = 0
        elif self.direction.x:
            self.frame_index += self.animation_speed * dt
            self.flip = self.direction.x < 0

        if not self.on_floor:
            self.frame_index = 1

        self.image = self.frames[int(self.frame_index) % len(self.frames)]
        self.image = pygame.transform.flip(self.image, self.flip, False)

        
    def check_on_floor(self):

        bottom_rect = pygame.FRect((0,0) , (self.rect.width , 2)).move_to(midtop=self.rect.midbottom)
        self.on_floor = True if bottom_rect.collidelist([sprite.rect for sprite in self.collisions_sprites])  != -1 else False

    def collision(self, direction):
        for sprite in self.collisions_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: # moving right
                        self.rect.right = sprite.rect.left
                    if self.direction.x < 0: # moving left
                        self.rect.left = sprite.rect.right
                if direction == 'vertical':
                    if self.direction.y > 0: # moving down
                        self.rect.bottom = sprite.rect.top
                        self.direction.y = 0
                    if self.direction.y < 0: # moving up
                        self.rect.top = sprite.rect.bottom
                        self.direction.y = 0

class Enemy(Animation):
    def __init__(self, pos , frames , groups):
        super().__init__(pos , frames , groups)
        self.death_timer  = Timer(200 , func = self.kill)
        

    def destroy(self):
        self.death_timer.activate()
        self.animation_speed = 0
        self.image = pygame.mask.from_surface(self.image).to_surface()
        self.image.set_colorkey("black")

    def update(self , dt):
        self.death_timer.update() 
        if not self.death_timer:
            self.animate(dt)
            self.move(dt)
        
        

class Bees(Enemy):
    def __init__(self, pos , groups  , frames ,speed):
        super().__init__(pos , frames , groups)

        self.speed = speed
        self.amplitude = random.randint(500, 600)
        self.frequency = random.randint(400, 600)

    def bee_kill(self):
        if self.rect.right < -600:
            self.kill()    



    def move(self, dt):
        self.rect.x -= self.speed * dt
        self.rect.y += math.sin(pygame.time.get_ticks() / self.frequency ) * self.amplitude * dt
        self.bee_kill()


class Worms(Enemy):
    def __init__(self, rect, groups , frames ):
        super().__init__(rect.topleft , frames , groups)
        self.worm_rect = rect
        self.rect.bottomleft =  self.worm_rect.bottomleft

        self.direction = 1
        self.speed = random.randint(160, 200)
    
    def move(self, dt):
        self.rect.x += self.direction * self.speed * dt

    def constraint(self):
        if not self.worm_rect.contains(self.rect):
            self.direction *= -1
            self.frames = [pygame.transform.flip(surf , True, False) for surf in self.frames] 

    def update(self, dt):
        super().update(dt)
        if not self.death_timer:
            self.constraint()

        