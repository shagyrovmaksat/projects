#pylint: disable=no-member
import pygame
import random
import time
import pika
import json
from threading import Thread
from enum import Enum
import uuid
pygame.init()
#Screen
width = 1000
height = 600
#Colors
yellow = (255,255,0)
white = (255,255,255)
green = (0,255,0)
red = (255,0,0)
white = (255,255,255)
black = (0,0,0)
orange = (255,150,0)
button_yellow = (180,180,80)
button_green = (70,150,70)
button_red = (150,70,70)
#Sprites
walkup = pygame.image.load(r"sprites\up.png")
walkdown = pygame.image.load(r"sprites\down.png")
walkleft = pygame.image.load(r"sprites\left.png")
walkright = pygame.image.load(r"sprites\right.png")
enemyup = pygame.image.load(r"sprites\enemyup.png")
enemydown = pygame.image.load(r"sprites\enemydown.png")
enemyright = pygame.image.load(r"sprites\enemyright.png")
enemyleft = pygame.image.load(r"sprites\enemyleft.png")
bonusp = pygame.image.load(r"sprites\bonus.png")
wallp = pygame.image.load(r"sprites\wall.png")
control = pygame.image.load(r"sprites\control.png")
b1 = pygame.image.load(r"sprites\b1.png")
b2 = pygame.image.load(r"sprites\b2.png")
#Sounds
sound1 = pygame.mixer.Sound(r'sounds\shoot.wav')
sound2 = pygame.mixer.Sound(r'sounds\shoot2.wav')
sound3 = pygame.mixer.Sound(r'sounds\bonus.wav')
#Fonts
font1 = pygame.font.SysFont("Verdana.ttf", 90)
font2 = pygame.font.SysFont("Verdana.ttf", 60)
font3 = pygame.font.SysFont("Verdana.ttf", 30)
font4 = pygame.font.SysFont("Verdana.ttf", 25)
font5 = pygame.font.Font('freesansbold.ttf', 80)
#For animation
change = 1
ax=-600
ay=520
axs = 1
up = 100
r1 = pygame.image.load(r"sprites\r1.png")
r2 = pygame.image.load(r"sprites\r2.png")
l1 = pygame.image.load(r"sprites\l1.png")
l2 = pygame.image.load(r"sprites\l2.png")
map1 = pygame.image.load(r"maps\map1.png")
map2 = pygame.image.load(r"maps\map2.png")
map3 = pygame.image.load(r"maps\map3.png")
map4 = pygame.image.load(r"maps\map4.png")
#Main loops
menu = True
scene1 = True
scene2 = False
single = False
multi = False
multiAi = False
gameover = False
takebonus = False
in_single = False
in_multi = False
in_multiai = False
you_were_kicked = False
you_win = False
you_lose = False
max_players = False
#Screen
screen = pygame.display.set_mode((width,height))
pygame.display.set_caption("Tank")
ic = pygame.image.load(r'sprites\tank.png')
pygame.display.set_icon(ic)

bullets = []
walls = []
right = 1
left = 2
up = 3
down = 4
lb1 = True
lb2 = False
ib1 = 10
ib2 = 0
room = 0
m = 0
score = 0
myhelath = 0
MOVE_KEYS = {pygame.K_UP : 'UP', pygame.K_RIGHT : 'RIGHT', pygame.K_LEFT : 'LEFT', pygame.K_DOWN : 'DOWN'}
Direction = ['UP','DOWN','RIGHT','LEFT']

class Client:

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('34.254.177.17', 5672, 'dar-tanks', pika.PlainCredentials('dar-tanks', password='5orPLExUYnyVYZg48caMpX')))

        self.channel = self.connection.channel()                 
        queue = self.channel.queue_declare(
            queue='', exclusive=True, auto_delete=True)
        self.callback_queue = queue.method.queue
        self.channel.queue_bind(
            exchange='X:routing.topic', queue=self.callback_queue)
        self.channel.basic_consume(queue=self.callback_queue,
                                   on_message_callback=self.on_response,
                                   auto_ack=True) 

        self.response = None
        self.corr_id = None
        self.token = None
        self.tank_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = json.loads(body)
            #print(self.response)

    def call(self, key, message={}): 
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='X:routing.topic',
            routing_key=key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=json.dumps(message)  
        )
        while self.response is None:
            self.connection.process_data_events()
        
        if key == 'tank.request.fire':
            if self.response.get('status', 200) == 200: sound1.play()
            else: pass

    def obtain_token(self, room_id):
        message = {
            'roomId': room_id
        }
        self.call('tank.request.register', message)
        if 'token' in self.response:
            self.token = self.response['token']
            self.tank_id = self.response['tankId']
            self.room_id = self.response['roomId']
            return True
        return False

    def turn_tank(self, token, direction):
        message = {
            'token': token,
            'direction': direction
        }
        self.call('tank.request.turn', message)
    
    def fire_bullet(self, token):
        message = {
            'token': token
        }
        self.call('tank.request.fire', message)
    
    def closed(self):    
        self.channel.stop_consuming()

class Server(Thread):

    def __init__(self, room_id):
        super().__init__()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('34.254.177.17', 5672, 'dar-tanks', pika.PlainCredentials('dar-tanks', password='5orPLExUYnyVYZg48caMpX')))

        self.channel = self.connection.channel()
        queue = self.channel.queue_declare(queue='',
                                           exclusive=True,
                                           auto_delete=True
                                           )
        event_listener = queue.method.queue
        self.channel.queue_bind(exchange='X:routing.topic',
                                queue = event_listener,
                                routing_key='event.state.{}'.format(room_id)
                                )
        self.channel.basic_consume(
            queue=event_listener,
            on_message_callback=self.on_response,
            auto_ack=True
        )
        self.response = None

    def on_response(self, ch, method, props, body):
        self.response = json.loads(body)
        #print(self.response)

    def run(self):
        self.channel.start_consuming()
    
    def closed(self):    
        self.channel.stop_consuming()

class Bonus:

    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.width = 31
        self.height = 31
        self.time = 10
    
    def draw(self):
        screen.blit(bonusp, (self.x, self.y))

class Wall:

    def __init__(self,x,y,drawing):
        self.x = x-29
        self.y = y-29
        self.width = 30
        self.height = 30
        self.drawing = drawing

    def draw(self):
        screen.blit(wallp, (self.x, self.y))

class Bullet:

    def __init__(self,x,y,direction):
        self.x = x
        self.y = y
        self.color = white 
        self.direction = direction
        self.speed = 10
    
    def move(self):
        if self.direction == right:
            self.x += self.speed
        elif self.direction == left:
            self.x -= self.speed
        elif self.direction == up:
            self.y -= self.speed
        elif self.direction == down:
            self.y += self.speed

        self.draw()
    
    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), 4)

class Tank:

    def __init__(self,x,y,direction,d_right = pygame.K_RIGHT, d_left = pygame.K_LEFT, d_up = pygame.K_UP, d_down = pygame.K_DOWN):
        self.x = x
        self.y = y
        self.width = 31
        self.height = 31
        self.reload = 500
        self.reloadb = 5000
        self.shootloop = 1
        self.bonusloop = 0
        self.seconds = 0
        self.secondsb = 0
        self.direction = direction
        self.speed = 5
        self.health = 3
        self.key = {d_right: right, d_left: left,
                    d_up: up, d_down: down}
    
    def change_direction(self, direction):
        self.direction = direction
    
    def ShootLoop(self):
        if pygame.time.get_ticks() > self.seconds + self.reload:
            self.shootloop = 0
    def BonusLoop(self):
        if pygame.time.get_ticks() > self.secondsb + self.reloadb:
            self.bonusloop = 0
    
    def draw(self):
        if self.direction == right:
            screen.blit(walkright, (self.x, self.y))
        if self.direction == left:
            screen.blit(walkleft, (self.x, self.y))
        if self.direction == up:
            screen.blit(walkup, (self.x, self.y))
        if self.direction == down:
            screen.blit(walkdown, (self.x, self.y))
        if self.bonusloop == True:
            if lb1 == True:
                screen.blit(b1, (mytank.x, mytank.y))
            if lb2 == True:
                screen.blit(b2, (mytank.x, mytank.y))
    
    def shoot(self):
        if self.shootloop == 0:
            sound1.play()
            if self.direction == left:
                bullet = Bullet(self.x, self.y + int(self.height/2), self.direction)
            if self.direction == right:
                bullet = Bullet(self.x + self.width, self.y + int(self.height/2), self.direction)
            if self.direction == up:
                bullet = Bullet(self.x + int(self.width/2), self.y, self.direction)
            if self.direction == down:
                bullet = Bullet(self.x + int(self.width/2), self.y + self.height, self.direction)
            bullets.append(bullet)
    
    def move(self):
        if self.direction == left:
            self.x -= self.speed
        if self.direction == right:
            self.x += self.speed
        if self.direction == up:
            self.y -= self.speed
        if self.direction == down:
            self.y += self.speed

        if self.x> 800:
            self.x = 0
        if self.x < 0:
           self.x = 800 
        if self.y < 0:
            self.y = 600
        if self.y> 600:
            self.y = 0
        
        self.draw()

def Single_Player_mode():
    global drawbonus, gameover, lb1, lb2, ib1, ib2, single, run
    map()
    drawbonus = False
    bonus = Bonus(random.randrange(0,700),random.randrange(0,500))
    bonus.time = 10
    clock = pygame.time.Clock()
    FPS = 30
    sec = (pygame.time.get_ticks())/1000
    run_single = True
    while run_single:
        mill = clock.tick(FPS)
        second = (pygame.time.get_ticks())/1000
        seconds = second - sec
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                    run_single = False
                if event.key in mytank.key.keys():
                    mytank.change_direction(mytank.key[event.key])
                    mytank.speed = 5
                if event.key == pygame.K_SPACE:
                    mytank.shoot()
                    mytank.seconds = pygame.time.get_ticks()
                    mytank.shootloop = 1
        
        screen.fill((0, 0, 0))
        if mytank.health == 0:
            gameover = True
            single = False
            run_single = False
            bonus.x = random.randrange(100,700)
            bonus.y = random.randrange(100,500)
        if mytank.shootloop == 1:
            mytank.ShootLoop()
        elif mytank.bonusloop == 1:
            mytank.BonusLoop()
        if lb1 == True and ib2 < ib1:
            ib2 += 1
        elif lb1 == True and ib2 >= ib1:
            ib2 += 10
            lb1 = False
            lb2 = True
        if lb2 == True and ib1 < ib2:
            ib1 += 1
        elif lb2 == True and ib1 >= ib2:
            ib1 += 10
            lb2 = False
            lb1 = True
    
        if drawbonus == True:
            bonus.draw()

        if mytank.bonusloop == 1 and mytank.speed != 0:
            mytank.speed = 10
            for bullet in bullets:
                bullet.speed = 20
        elif mytank.bonusloop == 0 and mytank.speed != 0:
            mytank.speed = 5
            for bullet in bullets:
                bullet.speed = 10
    
        if int(seconds) >= bonus.time and int(seconds) <= bonus.time + 5:
            drawbonus = True
        elif int(seconds) >= bonus.time and int(seconds) >= bonus.time + 5 and drawbonus == True:
            drawbonus = False
            bonus.time += 10
            bonus.x = random.randrange(100,700)
            bonus.y = random.randrange(100,500)

        if mytank.direction == left and drawbonus == True:
            if mytank.y in range(bonus.y-mytank.height,bonus.y+bonus.height) and mytank.x in range(bonus.x,bonus.x+bonus.width):
                sound3.play()
                mytank.secondsb = pygame.time.get_ticks()
                mytank.bonusloop = 1
                drawbonus = False
                bonus.time += 10
                bonus.x = random.randrange(100,700)
                bonus.y = random.randrange(100,500)
        elif mytank.direction == right and drawbonus == True:
            if mytank.y in range(bonus.y-mytank.height,bonus.y+bonus.height) and mytank.x in range(bonus.x-mytank.width,bonus.x+bonus.width):
                sound3.play()
                mytank.secondsb = pygame.time.get_ticks()
                mytank.bonusloop = 1
                drawbonus = False
                bonus.time += 10
                bonus.x = random.randrange(100,700)
                bonus.y = random.randrange(100,500)     
        elif mytank.direction == up and drawbonus == True:
            if mytank.x in range(bonus.x-mytank.width,bonus.x+bonus.width) and mytank.y in range(bonus.y,bonus.y+bonus.height):
                sound3.play()
                mytank.secondsb = pygame.time.get_ticks()
                mytank.bonusloop = 1
                drawbonus = False
                bonus.time += 10
                bonus.x = random.randrange(100,700)
                bonus.y = random.randrange(100,500)
        elif mytank.direction == down and drawbonus == True:
            if mytank.x in range(bonus.x-mytank.width,bonus.x+bonus.width) and mytank.y in range(bonus.y-mytank.height,bonus.y+bonus.height):
                sound3.play()
                mytank.secondsb = pygame.time.get_ticks()
                mytank.bonusloop = 1
                drawbonus = False
                bonus.time += 10
                bonus.x = random.randrange(100,700)
                bonus.y = random.randrange(100,500)
    
        for bullet in bullets:
            bullet.move()
            if bullet.x not in range(0,width) or bullet.y not in range(0,height):
                bullets.pop(0)
    
        for wall in walls:
            if wall.drawing == True:
                if bonus.x in range(wall.x-bonus.width,wall.x+wall.width) and bonus.y in range(wall.y-bonus.height, wall.y + wall.height):
                    bonus.x = random.randrange(100,700)
                    bonus.y = random.randrange(100,500)
                wall.draw()
                if mytank.direction == left:
                    if mytank.y in range(wall.y-mytank.height,wall.y+wall.height) and mytank.x in range(wall.x,wall.x+wall.width):
                        mytank.speed = 0
                        mytank.x += 1
                if mytank.direction == right:
                    if mytank.y in range(wall.y-mytank.height,wall.y+wall.height) and mytank.x+mytank.width in range(wall.x,wall.x+wall.width):
                        mytank.speed = 0
                        mytank.x -= 1
                if mytank.direction == up:
                    if mytank.x in range(wall.x-mytank.width,wall.x+wall.width) and mytank.y in range(wall.y,wall.y+wall.height):
                        mytank.speed = 0
                        mytank.y += 1
                if mytank.direction == down:
                    if mytank.x in range(wall.x-mytank.width,wall.x+wall.width) and mytank.y+mytank.height in range(wall.y,wall.y+wall.height):
                        mytank.speed = 0
                        mytank.y -= 1
                for bullet in bullets:
                    if bullet.x in range(wall.x, wall.x + wall.width) and bullet.y in range(wall.y, wall.y + wall.height):
                        sound2.play()
                        wall.drawing = False
                        mytank.health -= 1
                        bullets.pop(0)
    
        mytank.move()
        pygame.draw.rect(screen, white, (800,0,32,800))
        pygame.draw.rect(screen, black, (810,0,190,800))
        s1 = font3.render("Tank's health: " + str(mytank.health), True, white)
        screen.blit(s1, (825, 20))
        s2 = font3.render("Control buttons", True, white)
        textRect = s2.get_rect()
        textRect.center = (900, 500)
        screen.blit(s2, textRect)
        s3 = font3.render("Time: " + str(int(seconds)), True, white)
        screen.blit(s3, (825, 50))
        screen.blit(control, (840, 540))
        pygame.display.flip()

def Multiplayer_mode(room):
    global run, menu, multi, gameover, in_multi, you_were_kicked, you_win, you_lose, score, max_players, myhealth
    client = Client()
    play = True
    run_multi = True
    if client.obtain_token('room-{}'.format(room)) == False:
        play = False
        multi = False
        max_players = True
        run_multi = False
        menu = False 
    if play:
        event_client = Server('room-{}'.format(room))
        event_client.daemon = True
        event_client.start()
    
    #run_multi = True
    while run_multi:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_multi = False
                multi = False
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run_multi = False 
                    multi = False 
                    run = False            
                if event.key in MOVE_KEYS:
                    client.turn_tank(client.token, MOVE_KEYS[event.key])
                if event.key == pygame.K_SPACE:
                    # sound1.play()
                    client.fire_bullet(client.token)
        screen.fill((0,0,0))
        hits = event_client.response['hits']
        for tank in hits:
            if client.tank_id == tank["source"]:
               sound2.play() 
        kicked = event_client.response['kicked']
        for tank in kicked:
            if client.tank_id == tank["tankId"]:
                run_multi = False
                multi = False
                in_multi = False
                you_were_kicked = True
        winners = event_client.response['winners']
        for tank in winners:
            if client.tank_id == tank["tankId"]:
                run_multi = False
                multi = False
                in_multi = False
                you_win = True
        losers = event_client.response['losers']
        for tank in losers:
            if client.tank_id == tank["tankId"]:
                run_multi = False
                multi = False
                in_multi = False
                you_lose = True
        try:
            bullets = event_client.response['gameField']['bullets']
            tanks = event_client.response['gameField']['tanks']
            for bullet in bullets:
                bullet_x = bullet['x']
                bullet_y = bullet['y']
                bullet_w = bullet['width']
                bullet_h = bullet['height']
                if client.tank_id == bullet['owner']: pygame.draw.rect(screen, red, (bullet_x,bullet_y,bullet_w,bullet_h))
                else: pygame.draw.rect(screen, white, (bullet_x,bullet_y,bullet_w,bullet_h))
            scores = {}
            scores = {tank['id']: [tank['score'],tank['health']] for tank in tanks if tank['id'] != client.tank_id}
            sorted_scores = sorted(scores.items(), key=lambda kv: kv[1], reverse = True)
            for tank in tanks:
                tank_id = tank['id']
                tank_x = tank['x']
                tank_y = tank['y']
                tank_direction = tank['direction']
                if client.tank_id == tank['id']: 
                    score = tank["score"]
                    draw_tank(tank_x, tank_y, tank_direction, 'You')
                    myhealth = tank['health']
                else: draw_tank(tank_x, tank_y, tank_direction, tank_id)
            info_panel(client.tank_id, event_client.response['remainingTime'], myhealth, score)
            i = 110
            j = 0
            for tank in tanks:
                text2 = font4.render(sorted_scores[j][0]+':'+'  '+str(sorted_scores[j][1][1])+'  '+str(sorted_scores[j][1][0]), True, white)
                text2Rect = text2.get_rect()
                text2Rect.center = (900,i)
                screen.blit(text2, text2Rect)
                i += 20
                j += 1
        except Exception as e:
            #print(str(e))
            pass
        pygame.display.flip()
    try:
        client.closed()
        event_client.closed()
    except:
        pass

def Multiplayer_Ai_mode(room):
    global run, menu, multiAi, gameover, in_multiai, you_were_kicked, you_win, you_lose, score, myhealth, Direction, max_players
    client = Client()
    play = True
    run_multi_ai = True
    if client.obtain_token('room-{}'.format(room)) == False:
        play = False
        multiAi = False
        max_players = True
        run_multi_ai = False
        menu = False
    
    if play:
        event_client = Server('room-{}'.format(room))
        event_client.daemon = True
        event_client.start()
    
        sec = (pygame.time.get_ticks())/1000
        client.turn_tank(client.token, random.choice(Direction))
        ox_direction = ['RIGHT','LEFT']
        oy_direction = ['DOWN','UP']
        can = True
        ox = True
        oy = True
        one = True
        mytank_x = None
        mytank_y = None
        one_direction = [3,7,13,17,23,27,33,37,43,47,53,57,63,67,73,77,83,87,93,97,103,107,113,117,123,127]
        change_direction = []
        for i in range(5,121,5):
            change_direction.append(i)
    
    while run_multi_ai:
        Direction = ['UP','DOWN','RIGHT','LEFT']
        second = (pygame.time.get_ticks())/1000
        seconds = second - sec
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run_multi_ai = False
                multiAi = False
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run_multi_ai = False 
                    multiAi = False 
                    run = False
        screen.fill((0,0,0))
        hits = event_client.response['hits']
        for tank in hits:
            if client.tank_id == tank["source"]:
               sound2.play()
        losers = event_client.response['losers']
        for tank in losers:
            if client.tank_id == tank["tankId"]:
                run_multi_ai = False
                multiAi = False
                in_multiai = False
                you_lose = True
                can = False
        winners = event_client.response['winners']
        for tank in winners:
            if client.tank_id == tank["tankId"]:
                run_multi_ai = False
                multiAi = False
                in_multiai = False
                you_win = True 
                can =  False
        kicked = event_client.response['kicked']
        for tank in kicked:
            if client.tank_id == tank["tankId"]:
                run_multi_ai = False
                multiAi = False
                in_multiai = False
                you_were_kicked = True
                can = False
        if can:
            try:
                response = client.response
                if response.get('message', 400) == 'Invalid token':
                    run_multi_ai = False
                    multiAi = False
                    in_multiai = False
                    you_lose = True
                bullets = event_client.response['gameField']['bullets']
                tanks = event_client.response['gameField']['tanks']

                if int(seconds) in one_direction:
                    one = True
                if int(seconds) in change_direction and one == True:
                    for tank in tanks:
                        if tank['id'] == client.tank_id:
                            one = False
                            if tank['direction'] == 'UP':
                                Direction.pop(0)
                                client.turn_tank(client.token, random.choice(Direction))
                            elif tank['direction'] == 'DOWN':
                                Direction.pop(1)
                                client.turn_tank(client.token, random.choice(Direction))
                            elif tank['direction'] == 'RIGHT':
                                Direction.pop(2)
                                client.turn_tank(client.token, random.choice(Direction))
                            else:
                                Direction.pop(3)
                                client.turn_tank(client.token, random.choice(Direction))
            
                for bullet in bullets:
                    bullet_x = bullet['x']
                    bullet_y = bullet['y']
                    bullet_w = bullet['width']
                    bullet_h = bullet['height']
                    if client.tank_id == bullet['owner']: pygame.draw.rect(screen, red, (bullet_x,bullet_y,bullet_w,bullet_h))
                    else: pygame.draw.rect(screen, white, (bullet_x,bullet_y,bullet_w,bullet_h))

                scores = {}
                scores = {tank['id']: [tank['score'],tank['health']] for tank in tanks if tank['id'] != client.tank_id}
                sorted_scores = sorted(scores.items(), key=lambda kv: kv[1], reverse = True)
                for tank in tanks:
                    tank_id = tank['id']
                    tank_x = tank['x']
                    tank_y = tank['y']
                    tank_direction = tank['direction']
                    if client.tank_id == tank['id']:
                        mytank_x = tank_x
                        mytank_y = tank_y 
                        draw_tank(tank_x, tank_y, tank_direction, 'You')
                        myhealth = tank['health']
                        score = tank['score']
                    else: draw_tank(tank_x, tank_y, tank_direction, tank_id)
  
                info_panel(client.tank_id, event_client.response['remainingTime'], myhealth, score)                                
                i = 110
                j = 0
                for tank in tanks:
                    if client.tank_id != tank['id']: 
                        text2 = font4.render(sorted_scores[j][0]+':'+'  '+str(sorted_scores[j][1][1])+'  '+str(sorted_scores[j][1][0]), True, white)
                        text2Rect = text2.get_rect()
                        text2Rect.center = (900,i)
                        screen.blit(text2, text2Rect)
                        i += 20
                        j += 1
   
                for bullet in bullets:
                    if bullet["owner"] != client.tank_id:
                        if bullet['x'] in range(mytank_x-31,mytank_x+31):
                            if mytank_y > bullet_y:
                                if mytank_y - bullet_y <= 250:
                                    if ox == True:
                                        client.turn_tank(client.token, random.choice(ox_direction))
                                        ox = False
                            elif mytank_y < bullet_y:
                                if bullet_y - mytank_y <= 250:
                                    if ox == True:
                                        client.turn_tank(client.token, random.choice(ox_direction))
                                        ox = False
                        else: ox = True
                        if bullet['y'] in range(mytank_y-31,mytank_y+31):
                            if mytank_x > bullet_x:
                                if mytank_x - bullet_x <= 250:
                                    if oy == True:
                                        client.turn_tank(client.token, random.choice(oy_direction))
                                        oy = False
                            elif mytank_x < bullet_x:
                                if bullet_x - mytank_x <= 250:
                                    if oy == True:
                                        client.turn_tank(client.token, random.choice(oy_direction))
                                        oy = False
                        else: oy = True

                for tank in tanks:
                    tank_id = tank['id']
                    tank_x = tank['x']
                    tank_y = tank['y']
                    if client.tank_id != tank['id']: 
                    #Fire
                        if mytank_x in range(tank_x, tank_x+31) and tank_y > mytank_y:
                            if tank_y - mytank_y <= 300:
                                client.turn_tank(client.token, 'DOWN')
                                client.fire_bullet(client.token)
                                client.turn_tank(client.token, random.choice(ox_direction))
                            else:
                                client.turn_tank(client.token, 'UP')
                                client.fire_bullet(client.token)
                                client.turn_tank(client.token, random.choice(ox_direction))
                        elif mytank_x in range(tank_x, tank_x+31) and tank_y < mytank_y:
                            if mytank_y - tank_y <= 300:
                                client.turn_tank(client.token, 'UP')
                                client.fire_bullet(client.token)
                                client.turn_tank(client.token, random.choice(ox_direction))
                            else:
                                client.turn_tank(client.token, 'DOWN')
                                client.fire_bullet(client.token)
                                client.turn_tank(client.token, random.choice(ox_direction))
                        elif mytank_y in range(tank_y, tank_y+31) and tank_x > mytank_x:
                            if tank_x - mytank_x <= 300:
                                client.turn_tank(client.token, 'RIGHT')
                                client.fire_bullet(client.token)
                                client.turn_tank(client.token, random.choice(oy_direction))
                            else:
                                client.turn_tank(client.token, 'LEFT')
                                client.fire_bullet(client.token)
                                client.turn_tank(client.token, random.choice(oy_direction))
                        elif mytank_y in range(tank_y, tank_y+31) and tank_x < mytank_x:
                            if mytank_x - tank_x <= 300:
                                client.turn_tank(client.token, 'LEFT')
                                client.fire_bullet(client.token)
                                client.turn_tank(client.token, random.choice(oy_direction))
                            else:
                                client.turn_tank(client.token, 'RIGHT')
                                client.fire_bullet(client.token)
                                client.turn_tank(client.token, random.choice(oy_direction))
  
            except Exception as e:
                # print(e)
                pass
            pygame.display.flip()
    try:
        client.closed()
        event_client.closed()
    except:
        pass

def draw_tank(x, y, direction, id):
    if id == 'You':
        if direction == 'UP':
            screen.blit(walkup, (x, y))
        elif direction == 'DOWN':
            screen.blit(walkdown, (x, y))
        elif direction == 'RIGHT':
            screen.blit(walkright, (x, y))
        elif direction == 'LEFT':
            screen.blit(walkleft, (x, y))       
    else:
        text = font4.render(id, True, (255, 255, 255))
        screen.blit(text, (x-5,y-18))
        if direction == 'UP':
            screen.blit(enemyup, (x, y))
        elif direction == 'DOWN':
            screen.blit(enemydown, (x, y))
        elif direction == 'RIGHT':
            screen.blit(enemyright, (x, y))
        elif direction == 'LEFT':
            screen.blit(enemyleft, (x, y)) 

def map():
    l=1
    f = open(r"maps\map{}.txt".format(m), "r")
    for line in f.readlines():
        for i in range(0,26):
            if line[i] == "@":
                wall=Wall((i+1)*30,l*30,True)
                walls.append(wall)
        l+=1

def animation():
    global ax, ay, axs, change, up
    if ax == 1800: 
        ax = -600
        up = -up
    if change == True:
        if up > 0:
            screen.blit(r1, (ax,ay))
            screen.blit(l1, (1000-ax-140,ay-100))
        else:
            screen.blit(r1, (ax,ay+up))
            screen.blit(l1, (1000-ax-140,ay-100-up))
    else:
        if up > 0:
            screen.blit(r2, (ax,ay))
            screen.blit(l2, (1000-ax-140,ay-100))
        else:
            screen.blit(r2, (ax,ay+up))
            screen.blit(l2, (1000-ax-140,ay-100-up))
    ax += axs
    change = -change

def info_panel(tank_id, time, health, score):
    me = tank_id
    remaining_time = time
    pygame.draw.rect(screen, white, (800,0,32,800))
    pygame.draw.rect(screen, black, (810,0,190,800))
    pygame.draw.rect(screen, white, (800,40,200,10))
    pygame.draw.rect(screen, white, (800,520,200,10))
    pygame.draw.rect(screen, green, (0,0,800,600), 3) 
    text = font4.render('Remaining Time: {}'.format(remaining_time), True, white)
    textRect = text.get_rect()
    textRect.center = (905, 25)
    screen.blit(text, textRect)
    pygame.draw.rect(screen, white, (1000,40,200,10))
    text1 = font4.render('Opponents', True, white)
    text1Rect = text1.get_rect()
    text1Rect.center = (900, 70)
    screen.blit(text1, text1Rect)
    text1 = font4.render('Health & Score', True, white)
    text1Rect = text1.get_rect()
    text1Rect.center = (900, 90)
    screen.blit(text1, text1Rect)
    text = font3.render('You: '+str(me), True, white)
    textRect = text.get_rect()
    textRect.center = (905, 545)
    screen.blit(text, textRect)
    text = font3.render('Your health: '+str(health), True, white)
    textRect = text.get_rect()
    textRect.center = (905, 565)
    screen.blit(text, textRect)
    text = font3.render('Your score: '+str(score), True, white)
    textRect = text.get_rect()
    textRect.center = (905, 585)
    screen.blit(text, textRect)

def button(text, x, y, width, height, inactive_color, active_color, action):
    global run, max_players, mytank, walls, bullets, scene1, scene2, menu, single, multi, multiAi, drawbonus, gameover, lb1, lb2, ib1, ib2, in_single, in_multi, in_multiai, room, m, you_were_kicked, you_lose, you_win
    
    cur = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x + width > cur[0] > x and y + height > cur[1] > y:
        pygame.draw.rect(screen, active_color, (x,y,width,height))
        if click[0] == 1:
            if action == "quit":
                run = False
            elif action == "play":
                scene1 = False
                scene2 = True
            elif action == "single":
                in_single = True
                scene1 = False
                scene2 = False
            elif action == "multi":
                in_multi = True
                scene1 = False
                scene2 = False
            elif action == "multi ai":
                in_multiai = True
                scene1 = False
                scene2 = False
            elif action == "back":
                if in_multi == True or in_multiai == True:
                    in_multiai = False
                    in_multi = False
                    scene1 = False
                    scene2 = True
                elif in_single == True:
                    in_single = False
                    scene1 = False
                    scene2 = True
                else:
                    scene1 = True
                    scene2 = False
            elif action == "restart":
                scene1 = True
                scene2 = False
                menu = True
                gameover = False
                single = False
                multi = False
                multiAi = False
                you_were_kicked = False
                you_win = False
                you_lose = False
                max_players = False
                walls.clear()
                bullets.clear()
                mytank.health = 3
                mytank = Tank(50,50,random.randrange(1,4))
                lb1 = True
                lb2 = False
                ib1 = 10
                ib2 = 0
                drawbonus = False
            for i in range(1, 31):
                if action == str(i):
                    if in_multi == True:
                        multi = True
                        room = i
                        menu = False
                    elif in_multiai == True:
                        multiAi = True
                        room = i
                        menu = False
            for i in range(1, 5):
                if action == "map{}".format(i):
                    if in_single:
                        in_single = False
                        m = i
                        menu = False
                        single = True
    else:
        pygame.draw.rect(screen, inactive_color, (x,y,width,height))
    
    textSurf = font3.render(text, True, black)
    textRect = textSurf.get_rect()
    textRect.center = ((x+(width/2)), y+(height/2))
    screen.blit(textSurf, textRect)

def show_menu():
    if scene1:
        text = font1.render('Welcome to The Tanks Game', True, white)
        textRect = text.get_rect()
        textRect.center = (500, 100)
        screen.blit(text, textRect)
        button("Play", 150,300,300,50, button_green, green, action="play")
        button("Quit", 550,300,300,50, button_red, red, action ="quit")
        animation() 
    elif scene2:
        text = font1.render('Choose a game mode', True, white)
        textRect = text.get_rect()
        textRect.center = (500, 100)
        screen.blit(text, textRect)
        button("Back", 750,520,200,50, button_red, red, action="back")
        button("Single player", 150,450,200,50, button_yellow, yellow, action="single")
        button("Multiplayer", 400,450,200,50, button_yellow, yellow, action ="multi")
        button("Multiplayer Ai", 650,450,200,50, button_yellow, yellow, action ="multi ai")
    elif in_single:
        text = font1.render('Choose a game map', True, white)
        textRect = text.get_rect()
        textRect.center = (500, 100)
        screen.blit(text, textRect)
        button("Back", 400,520,200,50, button_red, red, action="back")
        screen.blit(map1, (50, 150))
        screen.blit(map2, (650, 150))
        screen.blit(map3, (50, 350))
        screen.blit(map4, (650, 350))
        button("Map #1", 50,310,300,25, button_green, green, action="map1")
        button("Map #2", 650,310,300,25, button_green, green, action="map2")
        button("Map #3", 50,510,300,25, button_green, green, action="map3")
        button("Map #4", 650,510,300,25, button_green, green, action="map4")
    elif in_multi == True or in_multiai == True:
        text = font1.render('Choose a room', True, white)
        textRect = text.get_rect()
        textRect.center = (500, 100)
        screen.blit(text, textRect)
        button("Back", 400,520,200,50, button_red, red, action="back")
        x = 50
        y = 200
        for i in range(1, 31):
            button(str(i), x,y,90,50, button_green, green, action=str(i))
            x += 90
            if i == 10 or i == 20:
                x = 50
                y += 100

def gameover_menu(text, score = None):
    button("Restart", 150,500,300,50, button_green, green, action="restart")
    button("Quit", 550,500,300,50, button_red, red, action ="quit")
    color = (random.randrange(0,255),random.randrange(0,255),random.randrange(0,255))
    text = font1.render(text, True, color)
    textRect = text.get_rect()
    textRect.center = (500, 300)
    screen.blit(text, textRect)
    if score != None:
        text = font2.render("Your score: {}".format(score), True, color)
        textRect = text.get_rect()
        textRect.center = (500, 400)
        screen.blit(text, textRect)

def error_menu(text):
    button("Try", 150,500,300,50, button_green, green, action="restart")
    button("Quit", 550,500,300,50, button_red, red, action ="quit")
    color = (random.randrange(0,255),random.randrange(0,255),random.randrange(0,255))
    text = font3.render(text, True, color)
    textRect = text.get_rect()
    textRect.center = (500, 300)
    screen.blit(text, textRect)

mytank = Tank(50,50,random.randrange(1,4))

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                run = False

    screen.fill((0, 0, 0))
    if menu:
        show_menu()
    if gameover:
        gameover_menu("G A M E  O V E R") 
    
    if single:
        Single_Player_mode()  
    elif multi:
        Multiplayer_mode(room)
    elif multiAi:
        Multiplayer_Ai_mode(room)
    
    if you_were_kicked:
        gameover_menu("You were kicked!", score)
    elif you_win:
        gameover_menu("You won!" , score)
    elif you_lose:
        gameover_menu("You lose!", score)
    elif max_players:
        error_menu("Maximum number of players reached in this room. Try another room")
    pygame.display.flip()

pygame.quit()
