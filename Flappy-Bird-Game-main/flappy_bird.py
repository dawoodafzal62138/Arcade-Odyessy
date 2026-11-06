import random
import pygame
from sys import exit
from pathlib import Path

pygame.init()
Screen=pygame.display.set_mode((450,600) , pygame.SCALED)
pygame.display.set_caption("FLappy bird")
Clock=pygame.time.Clock()
Game_active=False
pipes=[]
score=0
event_input = True
bird_hit=False
show_gameover_screen=False

Current_dir = Path(__file__).parent.resolve()


bird0=pygame.image.load(f"{str(Current_dir)}/resourse_flappy/images/bird/flappybird0.png").convert_alpha()
bird1=pygame.image.load(f"{str(Current_dir)}/resourse_flappy/images/bird/flappybird1.png").convert_alpha()
bird2=pygame.image.load(f"{str(Current_dir)}/resourse_flappy/images/bird/flappybird2.png").convert_alpha()
bird3=pygame.image.load(f"{str(Current_dir)}/resourse_flappy/images/bird/flappybird3.png").convert_alpha()
bird_surface = [
    pygame.transform.scale(bird0, (55, 40)),
    pygame.transform.scale(bird1, (55, 40)),
    pygame.transform.scale(bird2, (55, 40)),
    pygame.transform.scale(bird3, (55, 40))
]
bird_surface_index=0
bird_surface_image=bird_surface[bird_surface_index]

pipeup_surface=pygame.image.load(f"{str(Current_dir)}/resourse_flappy/images/pipes/toppipe.png").convert_alpha()
pipeup_surface=pygame.transform.scale(pipeup_surface,(70,1000))

pipedown_surface=pygame.image.load(f"{str(Current_dir)}/resourse_flappy/images/pipes/bottompipe.png").convert_alpha()
pipedown_surface=pygame.transform.scale(pipedown_surface,(70,1000))
font1 = pygame.font.Font(f"{str(Current_dir)}/resourse_flappy/04B_19__.TTF", 50)
font2 = pygame.font.Font(f"{str(Current_dir)}/resourse_flappy/04B_19__.TTF", 35)

flappybird_image=pygame.image.load(f"{str(Current_dir)}/resourse_flappy/images/flappybird.png").convert_alpha()
flappybird_image=pygame.transform.scale(flappybird_image,(400,130))
flappybird_image_rect=flappybird_image.get_rect(center=(225,150))

button=pygame.image.load(f"{str(Current_dir)}/resourse_flappy/images/button_play.png")
button_image=pygame.transform.scale(button,(100,100))
button_rect=button_image.get_rect(center=(225,300))


background_image=pygame.image.load( f"{str(Current_dir)}/resourse_flappy/images/bird/background.png").convert_alpha()
background_image=pygame.transform.scale(background_image,(450,300))
background_image_rect=background_image.get_rect(center=(225,450))

gameover_image=pygame.image.load(f"{str(Current_dir)}/resourse_flappy/images/gameover.png").convert()
gameover_image_rect=gameover_image.get_rect(center=(225,150))


#Sound
background_sound=pygame.mixer.Sound(f"{str(Current_dir)}/resourse_flappy/music/bgm_mario.mp3")
die_sound=pygame.mixer.Sound(f"{str(Current_dir)}/resourse_flappy/music/sfx_die.wav")
hit_sound=pygame.mixer.Sound(f"{str(Current_dir)}/resourse_flappy/music/sfx_hit.wav")
point_sound=pygame.mixer.Sound(f"{str(Current_dir)}/resourse_flappy/music/sfx_point.wav")
jump_sound=pygame.mixer.Sound(f"{str(Current_dir)}/resourse_flappy/music/sfx_wing.wav")

background_sound.set_volume(0.3) 
jump_sound.set_volume(0.5)
point_sound.set_volume(0.7)
background_sound.play(loops=-1)
bird_gravity=0
def apply_gravity():
    global bird_gravity
    bird_gravity += 0.6
    bird_rect.y+=bird_gravity

def jump():
    global bird_gravity
    bird_gravity=-9

    
    
def pos():
    gap = 200
    gap_center = random.randint(150, 450)
    
    pipeup_rect = pipeup_surface.get_rect(midbottom=(500, gap_center - (gap / 2)))
    
    pipedown_rect = pipedown_surface.get_rect(midtop=(500, gap_center + (gap / 2)))
    
    return pipeup_rect, pipedown_rect

def draw_pipes(pipes):
    for pipe in pipes:
        if pipe.bottom >= 600:
            Screen.blit(pipedown_surface, pipe)
        else: 
            Screen.blit(pipeup_surface, pipe)

def pipes_movement(pipes):
    global score
    for pipe in pipes:
        pipe.x-=4
        if 48 < pipe.centerx <= 52:
            score+=0.5
            point_sound.play()
    return [pipe for pipe in pipes if pipe.x>-100]


    
    
def collision(pipes):
 
    for pipe in pipes:
        if bird_rect.colliderect(pipe):
            return False
    if bird_rect.top <= -50 or bird_rect.bottom >= 600:
        return False        
    return True 

def show_score():
    score_surface2=font2.render(str(int(score)),False,(0,0,0))
    score_surface1=font1.render(str(int(score)),False,(255,255,255))
    # Screen.blit(score_surface2,(224,49))
    Screen.blit(score_surface1,(225,50))
    


def get_bird_animation(index, surfaces):
    index += 0.15 
    if index >= len(surfaces):
        index = 0
    image = surfaces[int(index)]
    return index, image



bird_surface_image=bird_surface[bird_surface_index] 
bird_surface_image=pygame.transform.scale(bird_surface_image,(55,40))
bird_rect=bird_surface_image.get_rect(midbottom=(80,200))


pipe_event=pygame.USEREVENT + 1
pygame.time.set_timer(pipe_event,2000)
animation=pygame.USEREVENT+2
pygame.time.set_timer(animation,500)
while True:
 
    if Game_active:
        Screen.fill((139, 212, 245))
            
                        
        Screen.blit(background_image,background_image_rect)
        bird_surface_index,bird_surface_image = get_bird_animation(bird_surface_index,bird_surface)
        rotated_bird = pygame.transform.rotozoom(bird_surface_image, -bird_gravity * 3, 1)
        new_bird_rect=rotated_bird.get_rect(center=bird_rect.center)
        Screen.blit(rotated_bird,new_bird_rect) 
        draw_pipes(pipes)
        apply_gravity()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event_input:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()
                    if event.key == pygame.K_SPACE:
                        jump()
                        jump_sound.play()

                if event.type==pygame.MOUSEBUTTONDOWN:
                    jump()        
                    jump_sound.play()
                    

                if event.type == pipe_event:
                    pipes.extend(pos())


        if bird_hit==False:
            pipes=pipes_movement(pipes)
            show_score()

        if not bird_hit: 
            if collision(pipes) == False:
                bird_hit = True
                hit_sound.play()
                event_input = False
        if bird_hit == True and bird_rect.bottom >=600:
            bird_hit=False
            die_sound.play()
            Game_active=False
            event_input=True
            show_gameover_screen=True
        
        

    else:  
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type== pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    Game_active=True
                    bird_gravity=-9 
                    score=0
                    show_gameover_screen=False
        

        if show_gameover_screen== False:
            pipes.clear()
            bird_rect.y=200
            Screen.fill((139, 212, 245))
            Screen.blit(flappybird_image,flappybird_image_rect)
            Screen.blit(background_image,background_image_rect)
            Screen.blit(button_image,button_rect)
        else:
            pipes.clear()
            bird_rect.y=200
            Screen.fill((139, 212, 245))
            Screen.blit(gameover_image,gameover_image_rect)
            Screen.blit(background_image,background_image_rect)
            Screen.blit(button_image,button_rect)
            gameover_score=font2.render(f"Your Score: {int(score)}",False,(0,0,0))
            gameover_score_rect=gameover_score.get_rect(center=(225,450))
            Screen.blit(gameover_score,gameover_score_rect)
            


    
    pygame.display.update()
    Clock.tick(60)


