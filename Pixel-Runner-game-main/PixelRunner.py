import random
import pygame
import sys
from pathlib import Path

Current_dir = Path(__file__).parent.resolve()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        player_walk1=pygame.image.load(f"{Current_dir}/resources/graphics/Player/player_walk_1.png").convert_alpha()
        player_walk2=pygame.image.load(f"{Current_dir}/resources/graphics/Player/player_walk_2.png").convert_alpha()
        self.player_jump=pygame.image.load(f"{Current_dir}/resources/graphics/Player/jump.png").convert_alpha()
        self.player_walk=[player_walk1,player_walk2]
        self.player_index=0
        self.player_gravity=0       
        self.image=self.player_walk[self.player_index]
        self.rect=self.image.get_rect(midbottom=(80,300))
        self.jump_sound=pygame.mixer.Sound(f"{Current_dir}/resources/audio/jump.mp3")
        self.jump_sound.set_volume(0.4)
 
    def player_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.rect.bottom >= 300:
            self.jump_sound.play()
            self.player_gravity = -20

    def apply_gravity(self):
        self.player_gravity+=1
        self.rect.y+=self.player_gravity 
        if self.rect.bottom>=300:
            self.rect.bottom=300 

    def player_animation(self):
        if self.rect.bottom<300:
            self.image=self.player_jump
        else:
            self.player_index+=0.1
            if self.player_index>=len(self.player_walk):self.player_index=0 
            self.image=self.player_walk[int(self.player_index)]     


    def update(self):
        self.apply_gravity()
        self.player_input()                       
        self.player_animation()


class obstacle(pygame.sprite.Sprite):
    def __init__(self,type):
        super().__init__()
		
        if type == 'fly':
            fly_1 = pygame.image.load(f'{Current_dir}/resources/graphics/Fly/Fly1.png').convert_alpha()
            fly_2 = pygame.image.load(f'{Current_dir}/resources/graphics/Fly/Fly2.png').convert_alpha()
            self.frames = [fly_1,fly_2]
            y_pos = 170
        else:
            snail_1 = pygame.image.load(f'{Current_dir}/resources/graphics/snail/snail1.png').convert_alpha()
            snail_2 = pygame.image.load(f'{Current_dir}/resources/graphics/snail/snail2.png').convert_alpha()
            self.frames = [snail_1,snail_2]
            y_pos  = 300

        self.animation_index = 0
        self.image = self.frames[self.animation_index]
        self.rect = self.image.get_rect(midbottom = (random.randint(900,1100),y_pos))

    def obsatcle_animation(self):
        self.animation_index+=0.1
        if self.animation_index>=len(self.frames):self.animation_index=0 
        self.image=self.frames[int(self.animation_index)]


    def update_pos(self):
        self.obsatcle_animation()
        self.rect.x-=game_speed   
        self.destroy()
    def destroy(self):
        if self.rect.x<-100:
            self.kill()              

    def update(self):
        self.update_pos()


pygame.init()
screen=pygame.display.set_mode((800,400))
pygame.display.set_caption("Runner")
Clock=pygame.time.Clock()
game_font=pygame.font.Font(None,35)
Game_active=False
stop_time=0
score=0
game_speed=6
sky_surface=pygame.image.load(f"{Current_dir}/resources/graphics/Sky.png").convert()
ground_surface=pygame.image.load(f"{Current_dir}/resources/graphics/ground.png").convert()
music=pygame.mixer.Sound(f"{Current_dir}/resources/audio/music.wav")
music.play(loops=-1)
music.set_volume(0.1)
player=pygame.sprite.GroupSingle()
player.add(Player())
obstacle_group=pygame.sprite.Group()
def Display_score():
    current_time=int(pygame.time.get_ticks()/1000)-stop_time
    score_surface=game_font.render(f"Score: {current_time}",False,(64,64,64))
    score_rect=score_surface.get_rect(center=(400,50))
    screen.blit(score_surface,score_rect)
    return current_time

def collisions():
    if pygame.sprite.spritecollide(player.sprite,obstacle_group,False):
        obstacle_group.empty()
        return False
    else: return True

player_stand_surface=pygame.image.load(f"{Current_dir}/resources/graphics/Player/player_stand.png").convert_alpha()
player_stand_surface=pygame.transform.rotozoom(player_stand_surface,0,2)
player_stand_rect=player_stand_surface.get_rect(center=(400,200))

game_name_surface=game_font.render("Pixel runner",False,(111,196,169))
game_name_surface=pygame.transform.rotozoom(game_name_surface,0,1.5)
game_name_rect=game_name_surface.get_rect(center=(400,50))

game_message_surface=game_font.render("Press Space to Start",False,(111,196,169))
game_message_rect=game_message_surface.get_rect(center=(400,330))

obstacle_timer=pygame.USEREVENT + 1
pygame.time.set_timer(obstacle_timer,random.randint(1000,1800))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if Game_active:    
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        else:
            if event.type == pygame.KEYDOWN and event.key==pygame.K_SPACE:
                Game_active=True
                stop_time=int(pygame.time.get_ticks()/1000)
        if Game_active:
            if event.type==obstacle_timer:
                obstacle_group.add(obstacle(random.choice(["snail","fly","snail","snail"])))
             
    if Game_active:
        game_speed+=0.001
        screen.blit(sky_surface,(0,0))       
        screen.blit(ground_surface,(0,300))
        player.draw(screen)
        player.update()
        obstacle_group.draw(screen)
        obstacle_group.update()
        score=Display_score()
        Game_active=collisions()

    else:
        screen.fill((94,129,163))
        screen.blit(player_stand_surface,player_stand_rect)
        player.sprite.rect.midbottom=((80,300))
        gravity=0
        game_speed=6
        if score != 0: 
            score_message_surface=game_font.render(f"Score: {score}",False ,(64,64,64))
            score_message_rect=score_message_surface.get_rect(center=(400,90))
            screen.blit(score_message_surface,score_message_rect)
        
        screen.blit(game_name_surface,game_name_rect)
        screen.blit(game_message_surface,game_message_rect)
    pygame.display.update()
    Clock.tick(60)


