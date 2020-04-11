#pylint: disable=no-member
import pygame
import random

pygame.init()

screen = pygame.display.set_mode((800, 600))

class Snake:
    
    def __init__(self):
        self.size = 1  
        self.elements = [[100, 100]]
        self.dx = 8
        self.dy = 0
        self.is_add = False

    def draw(self):
        for element in self.elements:
            pygame.draw.rect(screen, (0, 255, 0), (element[0],element[1],20,20),3)

    def move(self):

        if self.is_add:
            self.size += 1
            self.elements.append([0, 0])
            self.is_add = False

        for i in range(len(self.elements) - 1, 0, -1):
            self.elements[i][0] = self.elements[i - 1][0]
            self.elements[i][1] = self.elements[i - 1][1]

        self.elements[0][0] += self.dx
        self.elements[0][1] += self.dy

        if(self.elements[0][1] < 0):
            self.elements[0][1] = 600
        if(self.elements[0][1] > 600):
            self.elements[0][1] = 0
        if(self.elements[0][0] < 0):
            self.elements[0][0] = 800
        if(self.elements[0][0] > 800):
            self.elements[0][0] = 0

class Apple:
    def __init__(self):
        self.x = random.randint(10, 780)
        self.y = random.randint(10, 570)

    def draw(self):
        pygame.draw.rect(screen, (255, 0, 0), (self.x,self.y,20,20))

snake = Snake()
apple = Apple()
d = 8       
  
FPS = 30
clock = pygame.time.Clock()

running = True
while running: 
    mill = clock.tick(FPS) 
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            running = False 
        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_ESCAPE: 
                running = False
            if event.key == pygame.K_RIGHT and snake.dx != -d:
                snake.dx = d 
                snake.dy = 0 
            if event.key == pygame.K_LEFT and snake.dx != d: 
                snake.dx = -d 
                snake.dy = 0 
            if event.key == pygame.K_UP and snake.dy != d : 
                snake.dx = 0 
                snake.dy = -d 
            if event.key == pygame.K_DOWN and snake.dy != -d: 
                snake.dx = 0 
                snake.dy = d 
            
    if snake.elements[0] in snake.elements[1:]:
        running = False
    if (apple.x >= snake.elements[0][0] - 20  and apple.x < snake.elements[0][0] + 20) and (apple.y >= snake.elements[0][1] - 20 and apple.y < snake.elements[0][1] + 20):
        apple.x = random.randint(10, 780)
        apple.y = random.randint(10, 570)
        snake.is_add = True

    snake.move()
    screen.fill((0, 0, 0))
    snake.draw()
    apple.draw()
    pygame.display.flip()