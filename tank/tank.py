#pylint: disable=no-member
import pygame
import random


pygame.init()
screen = pygame.display.set_mode((820,620))

class Direction:
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

class Bullet:

    def __init__(self, x, y, sx, sy):
        self.x = x
        self.y = y
        self.radius = 5
        self.speedx = sx
        self.speedy = sy

    def draw(self):
        pygame.draw.circle(screen, (0, 0, 0), (self.x, self.y), self.radius)
    
    def move(self):
        
        self.x += self.speedx
        self.y += self.speedy

        self.draw()

class Tank:

    def __init__(self, x, y, speed, color, d_right=pygame.K_RIGHT, d_left=pygame.K_LEFT, d_up=pygame.K_UP, d_down=pygame.K_DOWN):
        self.x = x
        self.y = y
        self.life = 3
        self.color = color
        self.speed = speed
        self.width = 40
        self.direction = random.randint(1, 4)
        
        self.KEY = {d_right: Direction.RIGHT, d_left: Direction.LEFT,
                    d_up: Direction.UP, d_down: Direction.DOWN}
    
    def draw(self):
        tank_c = (self.x + int(self.width/2), self.y + int(self.width/2))
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.width), 3)
        pygame.draw.circle(screen, self.color, tank_c, int(self.width/2))

        if self.direction == Direction.RIGHT:
            pygame.draw.line(screen, self.color, tank_c, (self.x + self.width + int(self.width/2), self.y + int(self.width / 2)), 8)
        if self.direction == Direction.LEFT:
            pygame.draw.line(screen, self.color, tank_c, (self.x - int(self.width/2), self.y + int(self.width / 2)), 8)
        if self.direction == Direction.UP:
            pygame.draw.line(screen, self.color, tank_c, (self.x + int(self.width/2), self.y - int(self.width / 2)), 8)
        if self.direction == Direction.DOWN:
            pygame.draw.line(screen, self.color, tank_c, (self.x + int(self.width/2), self.y + self.width + int(self.width / 2)), 8)  
    
    def change_direction(self, direction):
        self.direction = direction

    def move(self):
        if self.direction == Direction.LEFT:
            self.x -= self.speed
        if self.direction == Direction.RIGHT:
            self.x += self.speed
        if self.direction == Direction.UP:
            self.y -= self.speed
        if self.direction == Direction.DOWN:
            self.y += self.speed

        if self.y < -40:
            self.y = 600
        if self.y > 600:
            self.y = 0
        if self.x < -40:
            self.x = 800
        if self.x > 800:
            self.x = 0
        
        self.draw()

def Life1(x):
    font = pygame.font.SysFont("Verdana.ttf", 25)
    pnt = font.render("Player1: " + str(x), True, (0, 0, 0))
    screen.blit(pnt, (20, 20))

def Life2(x):
    font = pygame.font.SysFont("Verdana.ttf", 25)
    pnt = font.render("Player2: " + str(x), True, (0, 0, 0))
    screen.blit(pnt, (20, 40))

FPS = 30
clock = pygame.time.Clock()

tank1 = Tank(200, 300, 5, (0, 150, 0))
tank2 = Tank(500, 300, 5, (150, 0, 0), pygame.K_d, pygame.K_a, pygame.K_w, pygame.K_s)
sound1 = pygame.mixer.Sound('shoot1.wav')
sound2 = pygame.mixer.Sound('shoot2.wav')
bullet1 = Bullet(840,640,0,0)
bullet2 = Bullet(840,640,0,0)

run = True 
while run:
    mill = clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False
            if event.key in tank1.KEY.keys():
                tank1.change_direction(tank1.KEY[event.key])
            if event.key in tank2.KEY.keys():
                tank2.change_direction(tank2.KEY[event.key])

            if event.key == pygame.K_RETURN:
                sound1.play()
                if tank1.direction == Direction.LEFT:
                    bullet1.x = tank1.x - 20
                    bullet1.y = tank1.y + 20
                    bullet1.speedx = -10
                    bullet1.speedy = 0
                if tank1.direction == Direction.RIGHT:
                    bullet1.x = tank1.x + 60
                    bullet1.y = tank1.y + 20
                    bullet1.speedx = 10
                    bullet1.speedy = 0
                if tank1.direction == Direction.UP:
                    bullet1.x = tank1.x + 20
                    bullet1.y = tank1.y - 20
                    bullet1.speedx = 0
                    bullet1.speedy = -10
                if tank1.direction == Direction.DOWN:
                    bullet1.x = tank1.x + 20
                    bullet1.y = tank1.y + 60
                    bullet1.speedx = 0
                    bullet1.speedy = 10

            if event.key == pygame.K_SPACE:
                sound1.play()
                if tank2.direction == Direction.LEFT:
                    bullet2.x = tank2.x - 20
                    bullet2.y = tank2.y + 20
                    bullet2.speedx = -10
                    bullet2.speedy = 0
                if tank2.direction == Direction.RIGHT:
                    bullet2.x = tank2.x + 60
                    bullet2.y = tank2.y + 20
                    bullet2.speedx = 10
                    bullet2.speedy = 0
                if tank2.direction == Direction.UP:
                    bullet2.x = tank2.x + 20
                    bullet2.y = tank2.y - 20
                    bullet2.speedx = 0
                    bullet2.speedy = -10
                if tank2.direction == Direction.DOWN:
                    bullet2.x = tank2.x + 20
                    bullet2.y = tank2.y + 60
                    bullet2.speedx = 0
                    bullet2.speedy = 10
    
    if bullet1.x in range(tank2.x,tank2.x+40) and bullet1.y in range(tank2.y,tank2.y+40):
        sound2.play()
        tank2.life -= 1
        bullet1.x = 840
        bullet1.y = 640
        bullet1.speedx = 0
        bullet1.speedy = 0
    if bullet2.x in range(tank1.x,tank1.x+40) and bullet2.y in range(tank1.y,tank1.y+40):
        sound2.play()
        tank1.life -= 1
        bullet2.x = 840
        bullet2.y = 640
        bullet2.speedx = 0
        bullet2.speedy = 0

    if tank1.life == 0 or tank2.life == 0:
        run = False
    screen.fill((255, 255, 255))
    tank1.move()
    tank2.move()
    bullet1.move()
    bullet2.move()
    Life1(tank1.life)
    Life2(tank2.life)
    pygame.display.flip()

pygame.quit()