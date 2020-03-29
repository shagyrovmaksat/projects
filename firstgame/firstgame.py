#pylint: disable=no-member
import pygame
import random

pygame.init()

screen = pygame.display.set_mode((600, 600))

background_image = pygame.image.load("background.jpg")

bullet_image = pygame.image.load("bullet.png")
bullet_y = 600
bullet_x = 0 
bullet_dy = 3

player_image = pygame.image.load("player.png")
player_x = 260
player_y = 513

enemy_image = pygame.image.load("enemy.png")
enemy_x = random.randint(1, 534)
enemy_y = random.randint(20, 50)
enemy_dx = 1
enemy_dy = 30

hit = False
press = False
shoot = False

def player(x, y): screen.blit(player_image,(x,y))
def enemy(x, y): screen.blit(enemy_image,(x,y))
def bullet(x,y): screen.blit(bullet_image,(x,y))

done = False
while not done:
    pressed = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if pressed[pygame.K_SPACE] and press is False:
            bullet_y = 480
            bullet_x = player_x + 20
            press = True
            shoot = True
    
    if enemy_x <= bullet_x <= enemy_x+50 and enemy_y <= bullet_y <= enemy_y+50:  
        bulet_y = 0
        bullet_x = 600
        hit = True
        enemy_x, enemy_y = random.randint(0, 534), random.randint(20, 50)

    if bullet_y == 0:
        shoot = False
        bullet_y = 600
        press = False

    if pressed[pygame.K_LEFT] and player_x >= 2: player_x -= 2.5
    if pressed[pygame.K_RIGHT] and player_x <= 534: player_x += 2.5

    enemy_x += enemy_dx
    if enemy_x < 0 or enemy_x > 536:
        enemy_dx = -enemy_dx
        enemy_y += enemy_dy

    if shoot is not False: bullet_y -= bullet_dy

    screen.blit(background_image, (0, 0))
    player(player_x, player_y)
    enemy(enemy_x,enemy_y)
    bullet(bullet_x, bullet_y)
    
    pygame.display.flip()