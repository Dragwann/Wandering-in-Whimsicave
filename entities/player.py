import pygame

from utilities.settings import WIDTH, HEIGHT, WHITE, BLUE, SHOW_HITBOXES
from utilities.utils import load_image
from projectiles.projectiles import Bullet

# Player Values
PLAYER_IMAGE = "entities/main_character.png"
PLAYER_DRAW_HEIGHT = 100
PLAYER_RADIUS = 25             # hitbox (circle)
PLAYER_SPEED = 320             # px/s
PLAYER_MAX_LIVES = 3           # normal mode (hard mode: Player(lives=1))
PLAYER_INVINCIBLE_TIME = 1.2   # seconds of invincibility after losing a life
PLAYER_SHOOT_COOLDOWN = 0.1
PLAYER_BULLET_SPEED = 520
PLAYER_BULLET_RADIUS = 5       # hitbox (circle)
PLAYER_BULLET_IMAGE = "projectiles/player_projectiles.png"
PLAYER_BULLET_HEIGHT = 24      # size of the shot on screen (px)


class Player:
    def __init__(self, lives=PLAYER_MAX_LIVES):
        self.x, self.y = 150, HEIGHT // 2
        self.radius = PLAYER_RADIUS
        self.max_lives = lives
        self.lives = lives
        self.invincible_timer = 0.0
        self.alive = True
        self.shoot_timer = 0.0
        self.image = load_image(PLAYER_IMAGE, height=PLAYER_DRAW_HEIGHT)
        self.bullet_image = load_image(PLAYER_BULLET_IMAGE, height=PLAYER_BULLET_HEIGHT)

    def update(self, dt, move_x, move_y, shooting, aim, bullets):
        # move_x / move_y come from read_input(): -1..1, keyboard or controller
        # aim is a unit vector (ax, ay): the direction the bullets will take
        self.x += move_x * PLAYER_SPEED * dt
        self.y += move_y * PLAYER_SPEED * dt
        self.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, self.x))
        self.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, self.y))

        if self.invincible_timer > 0:
            self.invincible_timer -= dt

        self.shoot_timer -= dt
        if shooting and self.shoot_timer <= 0:
            bullets.append(Bullet(self.x, self.y, aim[0] * PLAYER_BULLET_SPEED,
                                  aim[1] * PLAYER_BULLET_SPEED, PLAYER_BULLET_RADIUS, BLUE,
                                  self.bullet_image))
            self.shoot_timer = PLAYER_SHOOT_COOLDOWN

    def take_hit(self):
        """Lose one life. Returns False (nothing happens) while invincible."""
        if self.invincible_timer > 0 or self.lives <= 0:
            return False
        self.lives -= 1
        self.invincible_timer = PLAYER_INVINCIBLE_TIME
        return True

    def draw(self, surf):
        blinking = self.invincible_timer > 0 and int(self.invincible_timer * 10) % 2 == 0
        if not blinking:
            surf.blit(self.image, self.image.get_rect(center=(int(self.x), int(self.y))))
        if SHOW_HITBOXES:
            pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), PLAYER_RADIUS, 1)