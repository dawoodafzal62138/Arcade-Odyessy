from settings import *
from player import Player
from sprites import *
from groups import *
import time




class Game:
    def __init__(self):
        
        pygame.init()
        self.display_surface=pygame.display.set_mode((WIDTH,HEIGHT) , pygame.SCALED)
        self.display = pygame.Surface((WIDTH, HEIGHT))
        pygame.mouse.set_visible(True) 
        pygame.display.set_caption("Vampire Shooter")
        pygame.event.set_grab(True)
        self.Clock=pygame.time.Clock()
        self.running=True
        self.can_shoot=True
        self.shoot_time=0
        self.shoot_cooldown=100
        self.spawn_pos=[]
        self.last_damage_time=-600
        self.damage_cooldown=600

        # effects (same as ninja game)
        self.screenshake = 0
        self.transition = 0
        self.dead = 0

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

        self.start_image=pygame.transform.smoothscale(pygame.image.load(join("images","start.jpeg")).convert() , (WIDTH,HEIGHT))
        self.start_image_rect=self.start_image.get_rect(center=(WIDTH//2,HEIGHT//2))
        self.start_game = False 

        self.game_over_image=pygame.transform.smoothscale(pygame.image.load(join("images","gameover.jpeg")).convert() , (WIDTH,HEIGHT))
        self.game_over_image_rect=self.game_over_image.get_rect(center=(WIDTH//2,HEIGHT//2))
        self.game_over = False

        
        
        # setup
        self.load_images()
        self.setup()
        # enemy spawn timer: 0.5s between spawners, 2.0s before next round, 5 cycles max
        self.enemy_event = pygame.USEREVENT + 1
        self.current_spawn_index = 0
        self.cycle_count = 0
        self.max_cycles = 5
        pygame.time.set_timer(self.enemy_event, 500)

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

        # hearts (bright red color)
        heart_sheet = pygame.image.load(join("images", "16x16 Heart Health Red Horizontal.png")).convert_alpha()
        heart_full_raw = pygame.transform.scale2x(heart_sheet.subsurface((0, 0, 16, 16)))
        self.heart_full = heart_full_raw.copy()
        w, h = self.heart_full.get_size()
        for x in range(w):
            for y in range(h):
                r, g, b, a = self.heart_full.get_at((x, y))
                if a > 0 and (r > 60 or g > 40):
                    r = min(255, int(r * 1.8) + 30)
                    g = min(255, int(g * 1.1))
                    b = min(255, int(b * 1.1))
                    self.heart_full.set_at((x, y), (r, g, b, a))
        self.heart_empty = pygame.transform.scale2x(heart_sheet.subsurface((32, 0, 16, 16)))

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
        current_time = pygame.time.get_ticks()
        if current_time - self.last_damage_time > self.damage_cooldown:
            collided = pygame.sprite.spritecollide(self.player, self.enemy_sprite, False, pygame.sprite.collide_mask)
            living_collided = [e for e in collided if e.death_time == 0]
            if living_collided:
                self.impact_sound.play()
                self.player.health = max(0, self.player.health - 1)
                self.last_damage_time = current_time
                self.player.hit()
                for enemy_sprite in living_collided:
                    enemy_sprite.destroy()
                if self.player.health <= 0 and not self.dead:
                    self.dead = 1
                    self.screenshake = max(self.screenshake, 25)
                    self.transition = 0
                    self.player.kill()
                    self.gun.kill()
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

    def spawn_enemies(self):
        if not self.spawn_pos or self.cycle_count >= self.max_cycles:
            return

        pos = self.spawn_pos[self.current_spawn_index]
        enemy(
            choice(list(self.enemy_frames.values())),
            pos,
            self.player,
            self.collision_sprites,
            (self.all_sprites, self.enemy_sprite)
        )

        self.current_spawn_index += 1
        if self.current_spawn_index >= len(self.spawn_pos):
            self.current_spawn_index = 0
            self.cycle_count += 1
            if self.cycle_count >= self.max_cycles:
                pygame.time.set_timer(self.enemy_event, 0)
            else:
                # 2.0 sec delay after completing all spawners before restarting at spawner 1
                pygame.time.set_timer(self.enemy_event, 2000)
        else:
            # 0.5 sec delay before next spawner
            pygame.time.set_timer(self.enemy_event, 500)

    def health(self, target_surf=None):
        surf = target_surf if target_surf is not None else self.display_surface
        start_x = 20
        start_y = 20
        spacing = 38
        for i in range(self.player.max_health):
            x = start_x + i * spacing
            y = start_y
            if i < self.player.health:
                surf.blit(self.heart_full, (x, y))
            else:
                surf.blit(self.heart_empty, (x, y))

    def restart(self):
        self.all_sprites.empty()
        self.collision_sprites.empty()
        self.bullet_sprite.empty()
        self.enemy_sprite.empty()
        self.crosshair_sprite.empty()
        self.spawn_pos = []
        self.setup()
        cursor(self.cursor_image, self.crosshair_sprite)
        self.current_spawn_index = 0
        self.cycle_count = 0
        self.last_damage_time = -600
        self.can_shoot = True
        self.shoot_time = 0
        self.dead = 0
        self.screenshake = 16
        self.transition = -30
        self.game_over = False
        pygame.time.set_timer(self.enemy_event, 500)

    def run(self):
        while self.running:
            dt = self.Clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if not self.start_game:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            self.start_game = True
                            self.screenshake = 16
                            self.transition = -30
                            self.dead = 0
                            pygame.mouse.set_visible(False)
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.start_game = True
                        self.screenshake = 16
                        self.transition = -30
                        self.dead = 0
                        pygame.mouse.set_visible(False)

                elif self.game_over:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            self.restart()
                            pygame.mouse.set_visible(False)
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.restart()
                        pygame.mouse.set_visible(False)

                else:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                    elif event.type == self.enemy_event:
                        self.spawn_enemies()

            if not self.start_game:
                self.display_surface.blit(self.start_image, self.start_image_rect)
            elif self.game_over:
                self.display_surface.blit(self.game_over_image, self.game_over_image_rect)
            else:
                self.screenshake = max(0, self.screenshake - 1)

                if self.dead:
                    self.dead += 1
                    if self.dead >= 5:
                        self.transition = min(self.transition + 1, 30)
                    if self.dead > 35:
                        self.game_over = True
                        pygame.mouse.set_visible(True)
                elif self.transition < 0:
                    self.transition += 1

                if not self.dead:
                    self.input()
                    self.all_sprites.update(dt)
                    self.crosshair_sprite.update(dt)
                    self.collisions()
                    self.player_collision()
                else:
                    self.all_sprites.update(dt)
                    self.crosshair_sprite.update(dt)

                # Draw to offscreen display surface
                self.display.fill("black")
                self.all_sprites.draw(self.player.rect.center, self.display)
                if not self.dead:
                    self.crosshair_sprite.draw(self.display)
                self.health(self.display)

                # Transition circle effect (same as ninja game)
                if self.transition:
                    transition_surface = pygame.Surface(self.display.get_size())
                    radius = max(0, int((30 - abs(self.transition)) * 28))
                    if radius > 0:
                        pygame.draw.circle(transition_surface, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), radius)
                    transition_surface.set_colorkey((255, 255, 255))
                    self.display.blit(transition_surface, (0, 0))

                # Screenshake effect (same as ninja game)
                if self.screenshake:
                    screen_shake_offset = (randint(-self.screenshake, self.screenshake), randint(-self.screenshake, self.screenshake))
                else:
                    screen_shake_offset = (0, 0)

                self.display_surface.fill("black")
                self.display_surface.blit(self.display, screen_shake_offset)

            pygame.display.update()          
        pygame.quit()
        exit()



if __name__=="__main__":
    game=Game()
    game.run()