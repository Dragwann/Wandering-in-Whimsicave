import math
import pygame

from utilities.settings import WIDTH, HEIGHT, WARNING, PURPLE, RED, ORANGE
from utilities.utils import circle_hit

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
            pygame.draw.rect(surf, PURPLE, (int(self.x), self.y, self.w, self.h))


class Mine:
    """Motionless ring of bullets around a core. Harmless while arming, then deadly, then gone."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.age = 0.0
        self.dead = False

    def armed(self):
        return self.age >= MINE_ARM_TIME

    def update(self, dt, spawn=None):
        self.age += dt
        if self.age >= MINE_ARM_TIME + MINE_LIFETIME:
            self.dead = True

    def offscreen(self):
        return False   # a mine never moves, it only expires

    def ring_points(self):
        pts = []
        for i in range(MINE_COUNT):
            a = 2 * math.pi * i / MINE_COUNT
            pts.append((self.x + math.cos(a) * MINE_RING_RADIUS,
                        self.y + math.sin(a) * MINE_RING_RADIUS))
        return pts

    def hits(self, cx, cy, cr):
        if not self.armed():
            return False
        if circle_hit(self.x, self.y, MINE_CORE_RADIUS, cx, cy, cr):
            return True
        for px, py in self.ring_points():
            if circle_hit(px, py, MINE_DOT_RADIUS, cx, cy, cr):
                return True
        return False

    def draw(self, surf):
        if not self.armed():
            # warning: just an outline of the future mine
            pygame.draw.circle(surf, WARNING, (int(self.x), int(self.y)),
                               MINE_RING_RADIUS + MINE_DOT_RADIUS, 2)
            return
        remaining = MINE_ARM_TIME + MINE_LIFETIME - self.age
        if remaining < 0.8 and int(remaining * 10) % 2 == 0:
            return   # blink just before disappearing
        pygame.draw.circle(surf, RED, (int(self.x), int(self.y)), MINE_CORE_RADIUS)
        for px, py in self.ring_points():
            pygame.draw.circle(surf, ORANGE, (int(px), int(py)), MINE_DOT_RADIUS)
