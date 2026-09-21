import sys
import math
import pygame

# Config
WIDTH, HEIGHT = 960, 540
FPS = 60

# Player Values
PLAYER_RADIUS = 14
PLAYER_SHOOT_COOLDOWN = 0.1
PLAYER_BULLET_SPEED = 520
PLAYER_BULLET_RADIUS = 5

# Boss Values
BOSS_RADIUS = 55
BOSS_MAX_HP = 40
BOSS_BULLET_SPEED = 260
BOSS_BULLET_RADIUS = 8
BOSS_FIRE_COOLDOWN = 0.5

# Colors Values
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
RED = (220, 60, 60)
BLUE = (90, 160, 255)
PURPLE = (170, 90, 220)
GREEN = (90, 220, 120)

# Player Init
class Player:
    def __init__(self):
        self.x, self.y = 150, HEIGHT // 2
        self.alive = True
        self.shoot_timer = 0.0

    def update(self, dt, mouse_pos, shooting, bullets):
        # The player moves with mouse
        self.x, self.y = mouse_pos
        self.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, self.x))
        self.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, self.y))

        self.shoot_timer -= dt
        if shooting and self.shoot_timer <= 0:
            bullets.append(Bullet(self.x, self.y, PLAYER_BULLET_SPEED, 0, PLAYER_BULLET_RADIUS, BLUE))
            self.shoot_timer = PLAYER_SHOOT_COOLDOWN

    def draw(self, surf):
        pygame.draw.circle(surf, GREEN, (int(self.x), int(self.y)), PLAYER_RADIUS)


# Projectiles Init
class Bullet:
    def __init__(self, x, y, vx, vy, radius, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.radius = radius
        self.color = color

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def offscreen(self):
        return self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)


# Boss Init
class Boss:
    def __init__(self):
        self.x, self.y = WIDTH - 160, HEIGHT // 2
        self.hp = BOSS_MAX_HP
        self.t = 0.0
        self.fire_timer = 0.0

# Basic Movements
    def update(self, dt, bullets):
        self.t += dt
        self.y = HEIGHT // 2 + math.sin(self.t * 1.3) * 160

        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = BOSS_FIRE_COOLDOWN
            self.shoot(bullets)

# Basic Shooting patern
    def shoot(self, bullets):
        nb = 5
        spread = 0.6  # radians
        for i in range(nb):
            angle = math.pi + (i - (nb - 1) / 2) * (spread / (nb - 1))
            vx = math.cos(angle) * BOSS_BULLET_SPEED
            vy = math.sin(angle) * BOSS_BULLET_SPEED
            bullets.append(Bullet(self.x, self.y, vx, vy, BOSS_BULLET_RADIUS, PURPLE))

    def draw(self, surf):
        pygame.draw.circle(surf, RED, (int(self.x), int(self.y)), BOSS_RADIUS)
        # minimal health bar (no UI)
        ratio = max(self.hp, 0) / BOSS_MAX_HP
        pygame.draw.rect(surf, BLACK, (WIDTH // 2 - 152, 20, 304, 18))
        pygame.draw.rect(surf, RED, (WIDTH // 2 - 150, 22, int(300 * ratio), 14))


def circle_hit(x1, y1, r1, x2, y2, r2):
    return math.hypot(x1 - x2, y1 - y2) < (r1 + r2)

# Game Init
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wandering in Whimsicave (prototype)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28)
    pygame.mouse.set_visible(False)

    def new_game():
        return Player(), Boss(), [], [], "playing"

    player, boss, player_bullets, boss_bullets, state = new_game()

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and state != "playing":
                    player, boss, player_bullets, boss_bullets, state = new_game()

        mouse_pos = pygame.mouse.get_pos()
        shooting = pygame.mouse.get_pressed()[0]

        if state == "playing":
            player.update(dt, mouse_pos, shooting, player_bullets)
            boss.update(dt, boss_bullets)

            for b in player_bullets:
                b.update(dt)
            for b in boss_bullets:
                b.update(dt)

            player_bullets[:] = [b for b in player_bullets if not b.offscreen()]
            boss_bullets[:] = [b for b in boss_bullets if not b.offscreen()]

            # collisions : Player vs. boss shots
            still_alive_bullets = []
            for b in player_bullets:
                if circle_hit(b.x, b.y, b.radius, boss.x, boss.y, BOSS_RADIUS):
                    boss.hp -= 1
                else:
                    still_alive_bullets.append(b)
            player_bullets[:] = still_alive_bullets

            # collisions : boss shots vs player
            for b in boss_bullets:
                if circle_hit(b.x, b.y, b.radius, player.x, player.y, PLAYER_RADIUS):
                    state = "lose"
                    break

            if boss.hp <= 0:
                state = "win"

        # Drawing
        screen.fill((25, 20, 35))
        boss.draw(screen)
        for b in boss_bullets:
            b.draw(screen)
        for b in player_bullets:
            b.draw(screen)
        player.draw(screen)
        pygame.draw.circle(screen, WHITE, mouse_pos, 2)  

        if state == "win":
            txt = font.render("VICTOIRE ! Appuie sur R pour recommencer", True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 20))
        elif state == "lose":
            txt = font.render("TOUCHE... Appuie sur R pour reessayer", True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 20))

        pygame.display.flip()


if __name__ == "__main__":
    main()