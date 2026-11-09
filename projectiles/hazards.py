import math
import pygame

from utilities.settings import WIDTH, HEIGHT, WARNING, PURPLE, RED, ORANGE, SHOW_HITBOXES, WHITE
from utilities.utils import circle_hit, load_image

# Attack: big wall (covers 1/3 of the screen height)
TRUNK_IMAGE = "projectiles/tree_trunk.png" 
MINE_IMAGE = "projectiles/tornado.png"
MINE_DRAW_HEIGHT = 140         # taille de la tornade à l'écran (px), elle était à 70
MINE_HIT_RADIUS = 45           # hitbox (cercle), visible avec SHOW_HITBOXES : à ajuster sur la tornade
MINE_FLIP_INTERVAL = 0.15 

# Attack: big wall (covers 1/3 of the screen height)
WALL_WIDTH = 600
WALL_SPEED = 380
WALL_WARNING_TIME = 0.8        # lane is outlined before the wall becomes dangerous

# Boss 2: mines (a core + a ring of bullets, motionless)
MINE_ARM_TIME = 0.6            # harmless "warning" time after being dropped
MINE_LIFETIME = 3.5            # dangerous time
MINE_COUNT = 12                # bullets in the ring
MINE_RING_RADIUS = 36
MINE_DOT_RADIUS = 7
MINE_CORE_RADIUS = 12


class Wall:
    """Big rectangle covering one third of the screen height (lane 0/1/2 = top/middle/bottom)."""
 
    def __init__(self, lane):
        self.w = WALL_WIDTH
        self.h = HEIGHT // 3
        self.x = WIDTH
        self.y = lane * self.h
        self.warmup = WALL_WARNING_TIME
        self.dead = False
        self.image = load_image(TRUNK_IMAGE, size=(self.w, self.h))
 
    def update(self, dt, spawn=None):
        if self.warmup > 0:
            self.warmup -= dt
        else:
            self.x -= WALL_SPEED * dt
 
    def offscreen(self):
        return self.x + self.w < 0
 
    def hits(self, cx, cy, cr):
        if self.warmup > 0:      # harmless while it is only a warning
            return False
        # closest point of the rectangle to the circle center
        nx = max(self.x, min(cx, self.x + self.w))
        ny = max(self.y, min(cy, self.y + self.h))
        return math.hypot(cx - nx, cy - ny) < cr
 
    def draw(self, surf):
        if self.warmup > 0:
            pygame.draw.rect(surf, WARNING, (0, self.y, WIDTH, self.h), 3)
        else:
            surf.blit(self.image, (int(self.x), self.y))


class Mine:
    """Motionless tornado. Fades in and is harmless while arming, then deadly, then gone."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.age = 0.0
        self.dead = False
        img = load_image(MINE_IMAGE, height=MINE_DRAW_HEIGHT)
        # copies à elle (l'image en cache est partagée) pour que le fondu ne touche que cette mine
        self.frames = [img.copy(), pygame.transform.flip(img, True, False)]

    def armed(self):
        return self.age >= MINE_ARM_TIME

    def update(self, dt, spawn=None):
        self.age += dt
        if self.age >= MINE_ARM_TIME + MINE_LIFETIME:
            self.dead = True

    def offscreen(self):
        return False   # a mine never moves, it only expires

    def hits(self, cx, cy, cr):
        if not self.armed():
            return False
        return circle_hit(self.x, self.y, MINE_HIT_RADIUS, cx, cy, cr)

    def draw(self, surf):
        center = (int(self.x), int(self.y))
        if not self.armed():
            # warning : contour de la zone dangereuse + tornade qui apparaît en fondu
            pygame.draw.circle(surf, WARNING, center, MINE_HIT_RADIUS, 2)
            alpha = int(255 * self.age / MINE_ARM_TIME)
        else:
            remaining = MINE_ARM_TIME + MINE_LIFETIME - self.age
            if remaining < 0.8 and int(remaining * 10) % 2 == 0:
                return   # blink just before disappearing
            alpha = 255

        frame = self.frames[int(self.age / MINE_FLIP_INTERVAL) % 2]   # inversion gauche/droite
        frame.set_alpha(alpha)
        surf.blit(frame, frame.get_rect(center=center))
        if SHOW_HITBOXES:
            pygame.draw.circle(surf, WHITE, center, MINE_HIT_RADIUS, 1)
