import pygame

from utilities.settings import (WIDTH, HEIGHT, GREEN, BLUE, PLAYER_RADIUS, PLAYER_SPEED,
                      PLAYER_SHOOT_COOLDOWN, PLAYER_BULLET_SPEED, PLAYER_BULLET_RADIUS, SHOW_HITBOXES, WHITE)
from utilities.utils import load_image
from projectiles.projectiles import Bullet

PLAYER_IMAGE = "entities/main_character.png"
PLAYER_DRAW_HEIGHT = 100
PLAYER_BULLET_IMAGE = "projectiles/player_projectiles.png"
PLAYER_BULLET_HEIGHT = 30

class Player:
    def __init__(self):
        self.x, self.y = 150, HEIGHT // 2
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

        self.shoot_timer -= dt
        if shooting and self.shoot_timer <= 0:
            bullets.append(Bullet(self.x, self.y, PLAYER_BULLET_SPEED, 0, PLAYER_BULLET_RADIUS, BLUE, self.bullet_image))
            self.shoot_timer = PLAYER_SHOOT_COOLDOWN

    def draw(self, surf):
        surf.blit(self.image, self.image.get_rect(center=(int(self.x), int(self.y))))
        if SHOW_HITBOXES:
            pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), PLAYER_RADIUS, 1)
