# scorched earth battle game

# 1. Setup pygame window, clock, colors
# 2. Create Turret class (position, angle, power)
# 3. Create Terrain class (array of height values)
# 4. Implement player input handlers (arrow keys = angle, space = power/fire)
# 5. Add projectile physics:
#    - x = x0 + v0x * t
#    - y = y0 + v0y * t - 0.5 * g * t^2
# 6. Create collision detection (projectile vs terrain/turret)
# 7. Add terrain deformation (circular crater at impact)
# 8. Implement turn system (player 1/2)
# 9. Add win condition (turret destroyed)
# 10. Optional: wind effect, power meter, trajectory preview

# Critical math:
# - Initial velocity: (v0x = power * cos(angle), v0y = power * sin(angle))
# - Time step: position = previous_position + velocity * dt
# - Collision: check if projectile.y <= terrain_height[int(projectile.x)]

#!/usr/bin/env python3

from boil import *
from math import *
import random

game = init("Scorched Earth!", music="theme2", volume=0.3)

x0 = 50
y0 = 480
a0 = 30
h0 = 10
h1 = 10


b0 = False
bx0 = 400
by0 = 300
bxv0 = 5
byv0 = -5

b1 = False
bx1 = 600
by1 = 300
bxv1 = -5
byv1 = -5


x1 = 750
y1 = 480
a1 = 150

g = 0.1

tank_radius = 20

slope = random.uniform(-1/3, 1/3)

ground = [None] * game.width
for x in range(0, game.width):
    ground[x] = (x-game.width/2) * slope  + 2/3*game.height
    if x > 1/4*game.width and x< 3/4*game.width:
        ground[x] -= (game.width/4 - abs(x - game.width/2))*1.7


def kill_ground(xc):
    r = 50
    yc = ground[xc]
    for x in range(-r, r):
        # x^2 + y^2 = r^2
        y = sqrt(r*r - x*x)
        if xc + x >= 0 and xc + x <= game.width - 1:
            # ground goes down by max y, to depth max yc + y
            ground[xc + x] = max(ground[xc + x], min(ground[xc + x] + y, yc + y))

while playing():
    # draw ground
    # line ((0,500), (800,500))
    for x in range(0, game.width):
        y = ground[x]
        line((x,y), (x,game.height-1),(100, 50, 0))

    # put tanks on the ground
    y0 = ground[x0] - tank_radius
    y1 = ground[x1] - tank_radius

    # draw a circle for each player

    circle ((x0,y0), tank_radius)
    circle ((x1,y1), tank_radius)
   
    gl = tank_radius * 1.5

    gy0 = gl * sin(radians(a0))
    gx0 = gl * cos(radians(a0))
    # draw player 1's gun
    line ((x0,y0), (x0+gx0,y0-gy0))

    gy1 = gl * sin(radians(a1))
    gx1 = gl * cos(radians(a1))
    # draw player 1's gun
    line ((x1,y1), (x1+gx1,y1-gy1))

    # draw player bullets
    if b0:
        circle ((bx0,by0), 3, "red")
    if b1:
        circle ((bx1,by1), 3, "cyan")

    # update bullet positions
    if b0:
        bx0 += bxv0
        by0 += byv0

        byv0 += g
    if b1:
        bx1 += bxv1
        by1 += byv1

        byv1 += g

    # check if bullets goes off the screen
    if b0 and (by0 >= game.height or bx0 < 0 or bx0 >= game.width):
        b0 = False
    if b1 and (by1 >= game.height or bx1< 0 or bx1 >= game.width):
        b1 = False


    # check if bullets hit players

    # use Pythagores to work out distance from b0 to center of player 1's turret
    dx = x1 - bx0
    dy = y1 - by0
    d = sqrt(dx**2 + dy**2)
    if d <= 20 or y1 >= game.height:
        print ("boomp2!")
        h1 -= 1

    dx1 = x0 - bx1
    dy1 = y0 - by1
    d = sqrt(dx1**2 + dy1**2)
    if d <= 20 or y0 >= game.height:
        print ("boomp1!")
        h0 -= 1
    # controls

    # check for game over    
    if h0 < 1 or h1 < 1:
        break


    # check if bullets hit ground
    if b0 and by0 >= ground[int(bx0)]:
        kill_ground(int(bx0))
        b0 = False
    if b1 and by1 >= ground[int(bx1)]:
        kill_ground(int(bx1))
        b1 = False

    # draw health bars
    rect((0, 0), h0*5, 5, "green")
    rect((game.width-1 - h1*5, 0), h1*5, 5, "green")

    keys = pygame.key.get_pressed()

    if keys[pygame.K_w]:
        a0+=1
    if keys[pygame.K_s]:
        a0-=1
    if keys[pygame.K_SPACE] and not b0:
        bx0 = x0+gx0
        by0 = y0-gy0
        bxv0 = gx0/3
        byv0 = -gy0/3
        b0 = True
    if keys[pygame.K_a] and x0 > tank_radius:
        x0 -=1
    if keys[pygame.K_d]:
        x0 +=1


    if keys[pygame.K_UP]:
        a1-=1
    if keys[pygame.K_DOWN]:
        a1+=1
    if keys[pygame.K_RETURN] and not b1:
        bx1=x1+gx1
        by1=y1-gy1
        bxv1 = gx1/3
        byv1 = -gy1/3
        b1= True
        
    if keys[pygame.K_LEFT]:
        x1 -=1
    if keys[pygame.K_RIGHT] and x1 < game.width - tank_radius:
        x1 +=1