from settings import * 
from sprites import*

class Game(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        pygame.init()
        self.display_surface=pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
        pygame.display.set_caption("Pong Game")
        self.Clock=pygame.time.Clock()
        self.running=True
        #Groups
        self.all_sprite=pygame.sprite.Group()
        self.paddle_sprite=pygame.sprite.Group()
        self.player_1=player1((self.all_sprite,self.paddle_sprite))
        self.player_2=player2((self.all_sprite,self.paddle_sprite))
        ball(self.paddle_sprite,self.all_sprite)
        




    def run(self):
        while self.running:
            dt=self.Clock.tick(60)/1000
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    self.running=False
                if event.type==pygame.KEYDOWN:
                    if event.key== pygame.K_ESCAPE:
                        self.running=False  

            self.display_surface.fill(COLORS.get("bg"))
            # update
            self.all_sprite.update(dt)              
            #draw
            self.all_sprite.draw(self.display_surface)
            pygame.display.update()
        pygame.quit()
        exit()



if __name__ == "__main__":
    game=Game()
    game.run()
