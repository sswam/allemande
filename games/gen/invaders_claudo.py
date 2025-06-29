import pygame
import random
import math
from enum import Enum

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)

class PowerUpType(Enum):
    RAPID_FIRE = 1
    TRIPLE_SHOT = 2
    SHIELD = 3
    LASER = 4

class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.age = 0

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        self.vy += 200 * dt  # Gravity

    def draw(self, screen):
        alpha = 1 - (self.age / self.lifetime)
        if alpha > 0:
            size = int(3 * alpha)
            if size > 0:
                pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Fancy Space Invaders")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        self.reset_game()

    def reset_game(self):
        self.player_x = SCREEN_WIDTH // 2
        self.player_y = SCREEN_HEIGHT - 60
        self.player_speed = 300
        self.bullets = []
        self.enemies = []
        self.particles = []
        self.power_ups = []
        self.score = 0
        self.lives = 3
        self.wave = 1
        self.game_over = False

        # Power-up states
        self.rapid_fire = False
        self.triple_shot = False
        self.shield_active = False
        self.laser_mode = False
        self.power_up_timer = 0

        self.spawn_enemies()

    def spawn_enemies(self):
        rows = min(3 + self.wave // 2, 6)
        cols = min(8 + self.wave // 3, 12)

        for row in range(rows):
            for col in range(cols):
                x = 100 + col * 60
                y = 50 + row * 50
                enemy_type = random.choice(['basic', 'fast', 'tank']) if self.wave > 2 else 'basic'
                self.enemies.append({
                    'x': x, 'y': y,
                    'type': enemy_type,
                    'hp': 3 if enemy_type == 'tank' else 1,
                    'speed': 150 if enemy_type == 'fast' else 100,
                    'color': RED if enemy_type == 'tank' else GREEN if enemy_type == 'fast' else WHITE,
                    'size': 20 if enemy_type == 'tank' else 15,
                    'direction': 1
                })

    def create_explosion(self, x, y, color, intensity=20):
        for _ in range(intensity):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            self.particles.append(Particle(x, y, color, velocity, random.uniform(0.5, 1.5)))

    def handle_input(self, dt):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] and self.player_x > 30:
            self.player_x -= self.player_speed * dt
        if keys[pygame.K_RIGHT] and self.player_x < SCREEN_WIDTH - 30:
            self.player_x += self.player_speed * dt

    def shoot(self):
        if self.laser_mode:
            self.bullets.append({
                'x': self.player_x, 'y': self.player_y - 20,
                'type': 'laser', 'width': 4
            })
        elif self.triple_shot:
            for offset in [-20, 0, 20]:
                self.bullets.append({
                    'x': self.player_x + offset, 'y': self.player_y - 20,
                    'type': 'normal'
                })
        else:
            self.bullets.append({
                'x': self.player_x, 'y': self.player_y - 20,
                'type': 'normal'
            })

    def update(self, dt):
        if self.game_over:
            return

        self.handle_input(dt)

        # Update power-up timer
        if self.power_up_timer > 0:
            self.power_up_timer -= dt
            if self.power_up_timer <= 0:
                self.rapid_fire = False
                self.triple_shot = False
                self.shield_active = False
                self.laser_mode = False

        # Update bullets
        for bullet in self.bullets[:]:
            bullet['y'] -= 400 * dt
            if bullet['y'] < 0:
                self.bullets.remove(bullet)

        # Update enemies
        move_down = False
        for enemy in self.enemies:
            enemy['x'] += enemy['speed'] * enemy['direction'] * dt

            if enemy['x'] <= 20 or enemy['x'] >= SCREEN_WIDTH - 20:
                move_down = True

        if move_down:
            for enemy in self.enemies:
                enemy['direction'] *= -1
                enemy['y'] += 30

        # Enemy shooting
        if random.random() < 0.01:
            if self.enemies:
                shooter = random.choice(self.enemies)
                self.bullets.append({
                    'x': shooter['x'], 'y': shooter['y'] + 20,
                    'type': 'enemy', 'speed': 200
                })

        # Update enemy bullets
        for bullet in self.bullets[:]:
            if bullet.get('type') == 'enemy':
                bullet['y'] += bullet['speed'] * dt
                if bullet['y'] > SCREEN_HEIGHT:
                    self.bullets.remove(bullet)

        # Check collisions
        self.check_collisions()

        # Update particles
        for particle in self.particles[:]:
            particle.update(dt)
            if particle.age > particle.lifetime:
                self.particles.remove(particle)

        # Update power-ups
        for power_up in self.power_ups[:]:
            power_up['y'] += 100 * dt
            if power_up['y'] > SCREEN_HEIGHT:
                self.power_ups.remove(power_up)

        # Spawn power-ups
        if random.random() < 0.002:
            self.spawn_power_up()

        # Check wave completion
        if not self.enemies:
            self.wave += 1
            self.spawn_enemies()

    def spawn_power_up(self):
        x = random.randint(50, SCREEN_WIDTH - 50)
        power_type = random.choice(list(PowerUpType))
        self.power_ups.append({
            'x': x, 'y': 0,
            'type': power_type,
            'color': YELLOW if power_type == PowerUpType.RAPID_FIRE else
                     CYAN if power_type == PowerUpType.TRIPLE_SHOT else
                     BLUE if power_type == PowerUpType.SHIELD else PURPLE
        })

    def check_collisions(self):
        # Player bullets hitting enemies
        for bullet in self.bullets[:]:
            if bullet.get('type') != 'enemy':
                for enemy in self.enemies[:]:
                    if (abs(bullet['x'] - enemy['x']) < enemy['size'] and
                        abs(bullet['y'] - enemy['y']) < enemy['size']):

                        enemy['hp'] -= 1
                        if bullet.get('type') != 'laser':
                            self.bullets.remove(bullet)

                        if enemy['hp'] <= 0:
                            self.create_explosion(enemy['x'], enemy['y'], enemy['color'])
                            self.enemies.remove(enemy)
                            self.score += 100 * (2 if enemy['type'] == 'tank' else 1)
                        break

        # Enemy bullets hitting player
        for bullet in self.bullets[:]:
            if bullet.get('type') == 'enemy':
                if (abs(bullet['x'] - self.player_x) < 25 and
                    abs(bullet['y'] - self.player_y) < 25):

                    if self.shield_active:
                        self.create_explosion(bullet['x'], bullet['y'], BLUE, 10)
                    else:
                        self.lives -= 1
                        self.create_explosion(self.player_x, self.player_y, RED, 30)
                        if self.lives <= 0:
                            self.game_over = True

                    self.bullets.remove(bullet)

        # Power-up collection
        for power_up in self.power_ups[:]:
            if (abs(power_up['x'] - self.player_x) < 30 and
                abs(power_up['y'] - self.player_y) < 30):

                self.collect_power_up(power_up['type'])
                self.create_explosion(power_up['x'], power_up['y'], power_up['color'], 15)
                self.power_ups.remove(power_up)

    def collect_power_up(self, power_type):
        self.power_up_timer = 5.0  # 5 seconds duration

        if power_type == PowerUpType.RAPID_FIRE:
            self.rapid_fire = True
        elif power_type == PowerUpType.TRIPLE_SHOT:
            self.triple_shot = True
        elif power_type == PowerUpType.SHIELD:
            self.shield_active = True
        elif power_type == PowerUpType.LASER:
            self.laser_mode = True

    def draw(self):
        self.screen.fill(BLACK)

        # Draw stars background
        for _ in range(50):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(self.screen, WHITE, (x, y), 1)

        # Draw player
        pygame.draw.polygon(self.screen, CYAN, [
            (self.player_x, self.player_y - 20),
            (self.player_x - 20, self.player_y + 20),
            (self.player_x + 20, self.player_y + 20)
        ])

        if self.shield_active:
            pygame.draw.circle(self.screen, BLUE, (int(self.player_x), int(self.player_y)), 35, 2)

        # Draw enemies
        for enemy in self.enemies:
            pygame.draw.rect(self.screen, enemy['color'],
                           (enemy['x'] - enemy['size']//2, enemy['y'] - enemy['size']//2,
                            enemy['size'], enemy['size']))

        # Draw bullets
        for bullet in self.bullets:
            if bullet.get('type') == 'laser':
                pygame.draw.rect(self.screen, PURPLE,
                               (bullet['x'] - 2, 0, bullet['width'], bullet['y']))
            elif bullet.get('type') == 'enemy':
                pygame.draw.circle(self.screen, RED, (int(bullet['x']), int(bullet['y'])), 4)
            else:
                pygame.draw.circle(self.screen, YELLOW, (int(bullet['x']), int(bullet['y'])), 3)

        # Draw power-ups
        for power_up in self.power_ups:
            pygame.draw.rect(self.screen, power_up['color'],
                           (power_up['x'] - 15, power_up['y'] - 15, 30, 30), 2)
            pygame.draw.rect(self.screen, power_up['color'],
                           (power_up['x'] - 10, power_up['y'] - 10, 20, 20))

        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)

        # Draw UI
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 50))

        wave_text = self.font.render(f"Wave: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (SCREEN_WIDTH - 150, 10))

        if self.power_up_timer > 0:
            power_text = self.small_font.render(f"Power-up: {self.power_up_timer:.1f}s", True, YELLOW)
            self.screen.blit(power_text, (SCREEN_WIDTH//2 - 70, 10))

        if self.game_over:
            game_over_text = self.font.render("GAME OVER", True, RED)
            restart_text = self.small_font.render("Press R to restart", True, WHITE)
            self.screen.blit(game_over_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2))
            self.screen.blit(restart_text, (SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 + 40))

        pygame.display.flip()

    def run(self):
        running = True
        last_shot = 0

        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.game_over:
                        current_time = pygame.time.get_ticks()
                        shot_delay = 100 if self.rapid_fire else 250
                        if current_time - last_shot > shot_delay:
                            self.shoot()
                            last_shot = current_time
                    elif event.key == pygame.K_r and self.game_over:
                        self.reset_game()

            self.update(dt)
            self.draw()

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()

