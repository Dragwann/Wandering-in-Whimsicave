import math
import pygame

from utilities.settings import WHITE, WIDTH, HEIGHT, YELLOW, PURPLE, PINK, ORANGE, SHOW_HITBOXES
from utilities.utils import circle_hit, load_image

# Every hazard (Bullet and variants here, Wall and Mine in hazards.py) offers the same 5 things:
# update(dt, spawn), offscreen(), hits(cx, cy, cr), draw(surf) and a `dead` flag.
# `spawn` is a list a hazard can append new hazards to (used by the rain).

# Sprites (height in px on screen, width keeps the image ratio)
PINE_CONE_IMAGE = "projectiles/pine_cone.png"
LEAF_IMAGE = "projectiles/leaf.png"
PINE_CONE_HEIGHT = 50          # direct shots AND the rain fragments
PINE_CONE_BIG_HEIGHT = 70      # the big rain shell
LEAF_HEIGHT = 50  

TRAIL_IMAGE = "projectiles/lightning.png"
TRAIL_SPRITE_SCALE = 3   # hauteur du sprite = diamètre de la hitbox x ce nombre (1.0 = même taille)

# Attack: projectile rain (shell goes up, then splits into falling bullets)
RAIN_SHELL_SPEED = 420
RAIN_SHELL_RADIUS = 20
RAIN_SPLIT_Y = 60              # height where the shell splits
RAIN_COUNT = 8
RAIN_SPACING = 125             # horizontal gap between falling bullets
RAIN_SPEED = 250
RAIN_BULLET_RADIUS = 16

# Attack: sinusoidal projectile
WAVE_SPEED = 270
WAVE_RADIUS = 9
WAVE_AMPLITUDE = 90            # px, sideways swing around the straight path
WAVE_FREQ = 4.5                # rad/s

# Boss 2: dash trail
TRAIL_INTERVAL = 0.04          # seconds between two trail bullets
TRAIL_LIFETIME = 1.2
TRAIL_RADIUS = 8

def pine_cone(big=False):
    return load_image(PINE_CONE_IMAGE, height=PINE_CONE_BIG_HEIGHT if big else PINE_CONE_HEIGHT)
 
 
def leaf():
    return load_image(LEAF_IMAGE, height=LEAF_HEIGHT)


class Bullet:
    def __init__(self, x, y, vx, vy, radius, color, image=None):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.radius = radius
        self.color = color
        self.image = image
        self.dead = False

    def update(self, dt, spawn=None):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def offscreen(self):
        return self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20

    def hits(self, cx, cy, cr):
        return circle_hit(self.x, self.y, self.radius, cx, cy, cr)

    def draw(self, surf):
        if self.image:
            surf.blit(self.image, self.image.get_rect(center=(int(self.x), int(self.y))))
        else:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)


class RainShell(Bullet):
    """Large bullet that flies up, then splits into a row of falling bullets."""
 
    def __init__(self, x, y, vx, vy):
        super().__init__(x, y, vx, vy, RAIN_SHELL_RADIUS, YELLOW, pine_cone(big=True))
 
    def update(self, dt, spawn=None):
        super().update(dt)
        if self.y <= RAIN_SPLIT_Y:
            self.dead = True
            if spawn is not None:
                for i in range(RAIN_COUNT):
                    offset = (i - (RAIN_COUNT - 1) / 2) * RAIN_SPACING
                    spawn.append(Bullet(self.x + offset, RAIN_SPLIT_Y, 0, RAIN_SPEED,
                                        RAIN_BULLET_RADIUS, PURPLE, pine_cone()))


class WaveBullet(Bullet):
    """Bullet that follows a straight path but swings sideways like a sine wave."""
 
    def __init__(self, x, y, angle):
        super().__init__(x, y, 0, 0, WAVE_RADIUS, PINK, leaf())
        self.dir_x, self.dir_y = math.cos(angle), math.sin(angle)
        self.base_x, self.base_y = x, y   # position on the straight path
        self.t = 0.0
 
    def update(self, dt, spawn=None):
        self.t += dt
        self.base_x += self.dir_x * WAVE_SPEED * dt
        self.base_y += self.dir_y * WAVE_SPEED * dt
        # offset along the perpendicular of the travel direction
        offset = math.sin(self.t * WAVE_FREQ) * WAVE_AMPLITUDE
        self.x = self.base_x - self.dir_y * offset
        self.y = self.base_y + self.dir_x * offset


class TrailBullet(Bullet):
    """Motionless bullet left behind the dashing Boss 2. Shrinks, then disappears."""

    def __init__(self, x, y):
        super().__init__(x, y, 0, 0, TRAIL_RADIUS, ORANGE)
        self.life = TRAIL_LIFETIME

    def update(self, dt, spawn=None):
        self.life -= dt
        if self.life <= 0:
            self.dead = True
        # the visual AND the hitbox shrink together, so what you see is what hurts
        self.radius = max(2, int(TRAIL_RADIUS * self.life / TRAIL_LIFETIME))

    def draw(self, surf):
        height = max(4, int(2 * self.radius * TRAIL_SPRITE_SCALE))
        img = load_image(TRAIL_IMAGE, height=height)   # en cache : une copie redimensionnée par taille
        surf.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
        if SHOW_HITBOXES:
            pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.radius, 1)
