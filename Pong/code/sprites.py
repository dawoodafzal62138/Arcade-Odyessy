from settings import *
from random import choice , uniform


class paddle(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
    def __init__(self, *groups):
        super().__init__(*groups)
        self.image=pygame.Surface(SIZE.get("paddle"),pygame.SRCALPHA)
        paddle_color=COLORS.get("paddle1")
        pygame.draw.rect(self.image,paddle_color,pygame.FRect((0,0),SIZE.get("paddle")),0,8)
        self.player_pos=POS.get("player")
        self.rect=self.image.get_frect(center=self.player_pos)
        self.old_rect=self.rect.copy()
        self.direction=pygame.math.Vector2()
        self.speed=SPEED.get("player")


    def movement(self,dt):
        self.rect.centery+=self.speed*self.direction.y*dt
        if self.rect.top<0:self.rect.top=0
        if self.rect.bottom>WINDOW_HEIGHT:self.rect.bottom=WINDOW_HEIGHT


    def update(self,dt):
        self.old_rect=self.rect.copy()
        self.movement(dt)
        self.get_direction()


class player1(paddle):
    def __init__(self, *groups):
        super().__init__(*groups)


    def get_direction(self):
        keys=pygame.key.get_pressed()
        self.direction.y=int(keys[pygame.K_DOWN])-int(keys[pygame.K_UP])


class player2(paddle):
    def __init__(self, groups):
        super().__init__(groups)
        paddle_color=COLORS.get("paddle2")
        pygame.draw.rect(self.image,paddle_color,pygame.FRect((0,0),SIZE.get("paddle")),0,8)

        self.player_pos=POS.get("opponent")
        self.rect=self.image.get_frect(center=self.player_pos)

    def get_direction(self):
        keys=pygame.key.get_pressed()
        self.direction.y=int(keys[pygame.K_s])-int(keys[pygame.K_w])


class ball(pygame.sprite.Sprite):
    def __init__(self,paddle_sprite, groups):
        super().__init__(groups)
        self.paddle_sprite=paddle_sprite
        self.image=pygame.surface.Surface(SIZE.get("ball"),pygame.SRCALPHA)
        ball_width=SIZE.get("ball")[0]
        center_point=(ball_width//2,ball_width//2)
        radius=ball_width//2
        pygame.draw.circle(self.image,COLORS.get("ball"),center_point,radius)
        self.rect=self.image.get_frect(center=(WINDOW_WIDTH/2,WINDOW_HEIGHT/2))
        self.old_rect=self.rect.copy()
        
        self.direction=pygame.math.Vector2(choice((1,-1)),uniform(0.7,0.8)*choice((1,-1)))
        self.speed=SPEED.get("ball")

    def move(self,dt):
        self.rect.x+=self.speed*self.direction.x*dt
        self.collisions("horizontal")    
        self.rect.y+=self.speed*self.direction.y*dt
        self.collisions("vertical")    

        if self.rect.top<0:
            self.rect.top=0
            self.direction.y*=-1
        if self.rect.bottom>WINDOW_HEIGHT:
            self.rect.bottom=WINDOW_HEIGHT
            self.direction.y*=-1
        if self.rect.left<0:
            self.rect.left=0
            self.direction.x*=-1
        if self.rect.right>WINDOW_WIDTH:
            self.rect.right=WINDOW_WIDTH
            self.direction.x*=-1

    def collisions(self,direction):
        for sprite in self.paddle_sprite:
            if sprite.rect.colliderect(self.rect):
                if direction== "horizontal":
                    if self.rect.right>sprite.rect.left and self.old_rect.right<=sprite.old_rect.left:
                        self.rect.right=sprite.rect.left
                        self.direction.x*=-1
                    if self.rect.left<=sprite.rect.right and self.old_rect.left>=sprite.old_rect.right:
                        self.rect.left=sprite.rect.right
                        self.direction.x*=-1    
                else:
                    if self.rect.bottom>=sprite.rect.top and self.old_rect.bottom<=sprite.old_rect.top:
                        self.rect.bottom=sprite.rect.top
                        self.direction.y*=-1
                    if self.rect.top<=sprite.rect.bottom and self.old_rect.top>=sprite.old_rect.bottom:
                        self.rect.top=sprite.rect.bottom    
                        self.direction.y*=-1


    def update(self,dt):
        self.old_rect=self.rect.copy()
        self.move(dt)
        
        # if self.rect.colliderect(self.player.rect):
        #     self.direction.x=-1
        # if self.rect.colliderect(self.player2.rect):
        #     self.direction.x=1

