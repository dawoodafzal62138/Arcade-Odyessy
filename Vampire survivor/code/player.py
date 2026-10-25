from settings import *


        
class Player(pygame.sprite.Sprite):
    def __init__(self,pos, groups,collision_sprite):
        super().__init__(groups)
        self.load_images()
        self.frames_index ,self.state =0,"down"
        self.image=pygame.image.load(join("images","player","down","0.png")).convert_alpha()
        self.rect=self.image.get_frect(center=pos)
        self.hit_box=self.rect.inflate(-55,-90)
        self.collision_sprite=collision_sprite
        # movement
        self.direction=pygame.math.Vector2()
        self.speed=450
    
    # load all the images from different folder for player animation:  
    def load_images(self):
        self.frames={"left":[],"right":[],"up":[],"down":[],}
        for state in self.frames.keys():
            for folder_path ,sub_folder,file_names in walk(join("images","player",state)):
                if file_names:
                    for file_name in sorted(file_names,key=lambda name:int(name.split(".")[0])):
                        full_path=join(folder_path,file_name)
                        surface=pygame.image.load(full_path).convert_alpha()
                        self.frames[state].append(surface)

    def input(self):
        keys=pygame.key.get_pressed()
        self.direction.x=int(keys[pygame.K_RIGHT] or keys[pygame.K_d])-int(keys[pygame.K_LEFT] or keys[pygame.K_a])    
        self.direction.y=int(keys[pygame.K_DOWN] or keys[pygame.K_s])-int(keys[pygame.K_UP] or keys[pygame.K_w])
        if self.direction:
            self.direction=self.direction.normalize() 

    
    
    
    def movement(self,dt):
        self.hit_box.x+=self.direction.x*self.speed*dt
        self.collisions("horizontal") 
        self.hit_box.y+=self.direction.y*self.speed*dt 
        self.collisions("vertical") 
        self.rect.center=self.hit_box.center
        
    def collisions(self,diretion):
        for sprite in self.collision_sprite:
            if sprite.rect.colliderect(self.hit_box):
                if diretion == "horizontal":
                    if self.direction.x > 0: self.hit_box.right=sprite.rect.left
                    if self.direction.x < 0: self.hit_box.left=sprite.rect.right
                else:
                    if self.direction.y > 0: self.hit_box.bottom=sprite.rect.top
                    if self.direction.y < 0: self.hit_box.top=sprite.rect.bottom

    def animation(self,dt):
        # get state
        if self.direction.x!=0:
            if self.direction.x>0:self.state="right" 
            else: self.state="left"
        if self.direction.y!=0:
            if self.direction.y>0:self.state="down" 
            else: self.state="up"

    
        self.frames_index+=7*dt
        if self.direction.magnitude()==0:
            self.image=self.frames[self.state][0]
        else:
           
            self.image=self.frames[self.state][int(self.frames_index)%len(self.frames[self.state])]
    def update(self,dt):
        self.input()
        self.movement(dt)
        self.animation(dt)

