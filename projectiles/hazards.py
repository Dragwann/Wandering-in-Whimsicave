import pygame

from utilities.settings import WIDTH, HEIGHT, WARNING, WHITE
from utilities.utils import load_image
from utilities.hitbox import Hitbox
from utilities.placeholder import optional_image

# Same hazard contract as the bullets (see projectiles.py): update(dt, spawn), offscreen(),
# draw(surf), a `dead` flag and a `hitboxes` list.
# A hitbox is DISABLED while the hazard is only a warning: the CollisionManager then ignores it,
# and so does the debug drawing.

# Sprites (paths are relative to the assets folder)
TRUNK_IMAGE = "projectiles/tree_trunk.png"
MINE_IMAGE = "projectiles/tornado.png"
MINE_DRAW_HEIGHT = 140         # taille de la tornade à l'écran (px), elle était à 70
MINE_FLIP_INTERVAL = 0.15

# Attack: big wall (covers 1/3 of the screen height)
WALL_WIDTH = 600
WALL_SPEED = 380
WALL_WARNING_TIME = 0.8        # lane is outlined before the wall becomes dangerous

# Boss 2: mines (a motionless tornado)
MINE_HIT_RADIUS = 45           # hitbox (circle), visible with SHOW_HITBOXES : à ajuster sur la tornade
MINE_WARNING_RADIUS = MINE_HIT_RADIUS   # outline shown while arming = where it WILL hurt
MINE_ARM_TIME = 0.6            # harmless "warning" time after being dropped
MINE_LIFETIME = 3.5            # dangerous time

# Boss 3 (the Cutter): string shot downward by a hand
STRING_WIDTH = 22              # hitbox width = drawn width
STRING_TELEGRAPH_TIME = 0.9    # outline only, harmless
STRING_EXTEND_SPEED = 2600     # px/s, the string shoots down almost instantly
STRING_HOLD_TIME = 0.45        # fully extended and dangerous
STRING_RETRACT_SPEED = 3600    # px/s, pulled back up


class Wall:
    """Big rectangle covering one third of the screen height (lane 0/1/2 = top/middle/bottom).

    Its x, y is the TOP-LEFT corner (unlike everything else, which is center-based),
    so the hitbox is offset by half its size to sit on the wall.
    """

    def __init__(self, lane, image=None):
        self.w = WALL_WIDTH
        self.h = HEIGHT // 3
        self.x = WIDTH
        self.y = lane * self.h
        self.warmup = WALL_WARNING_TIME
        self.dead = False
        self.image = (optional_image(image, size=(self.w, self.h))
                  or load_image(TRUNK_IMAGE, size=(self.w, self.h)))
        # harmless while it is only a warning: enabled by update() once the warm-up is over
        self.hitboxes = [Hitbox.rect(self, self.w, self.h, offset=(self.w / 2, self.h / 2),
                                     enabled=False)]

    def update(self, dt, spawn=None):
        if self.warmup > 0:
            self.warmup -= dt
        else:
            self.x -= WALL_SPEED * dt
        self.hitboxes[0].enabled = self.warmup <= 0

    def offscreen(self):
        return self.x + self.w < 0

    def draw(self, surf):
        if self.warmup > 0:
            pygame.draw.rect(surf, WARNING, (0, self.y, WIDTH, self.h), 3)
        else:
            surf.blit(self.image, (int(self.x), self.y))


class Mine:
    """Motionless tornado. Fades in and is harmless while arming, then deadly, then gone."""

    def __init__(self, x, y, image=None, image_height=None):
        self.x, self.y = x, y
        self.age = 0.0
        self.dead = False
        img = (optional_image(image, height=image_height) or load_image(MINE_IMAGE, height=MINE_DRAW_HEIGHT))
        # copies à elle (l'image en cache est partagée) pour que le fondu ne touche que cette mine
        self.frames = [img.copy(), pygame.transform.flip(img, True, False)]
        # a mine must not hurt before it is armed: enabled by update() once MINE_ARM_TIME has passed
        self.hitboxes = [Hitbox.circle(self, MINE_HIT_RADIUS, enabled=False)]

    def armed(self):
        return self.age >= MINE_ARM_TIME

    def update(self, dt, spawn=None):
        self.age += dt
        if self.age >= MINE_ARM_TIME + MINE_LIFETIME:
            self.dead = True
        self.hitboxes[0].enabled = self.armed()

    def offscreen(self):
        return False   # a mine never moves, it only expires

    def draw(self, surf):
        center = (int(self.x), int(self.y))
        if not self.armed():
            # warning : contour de la zone dangereuse + tornade qui apparaît en fondu
            pygame.draw.circle(surf, WARNING, center, MINE_WARNING_RADIUS, 2)
            alpha = int(255 * self.age / MINE_ARM_TIME)
        else:
            remaining = MINE_ARM_TIME + MINE_LIFETIME - self.age
            if remaining < 0.8 and int(remaining * 10) % 2 == 0:
                return   # blink just before disappearing
            alpha = 255

        frame = self.frames[int(self.age / MINE_FLIP_INTERVAL) % 2]   # inversion gauche/droite
        frame.set_alpha(alpha)
        surf.blit(frame, frame.get_rect(center=center))


class String:
    """Vertical string shot downward from a hand (Boss 3, the Cutter).

    x, y = TOP-CENTER of the string (the anchor on the hand). Its hitbox is a rectangle whose height
    and offset follow `length` every frame, so what is drawn is exactly what hurts.
    States: telegraph (outline of the lane, harmless) -> extend -> hold -> retract -> dead.
    """

    def __init__(self, x, y, telegraph_time=STRING_TELEGRAPH_TIME):
        self.x, self.y = x, y
        self.max_length = HEIGHT - y
        self.length = 0.0
        self.state = "telegraph"
        self.timer = telegraph_time
        self.dead = False
        self.hitboxes = [Hitbox.rect(self, STRING_WIDTH, 0.0, enabled=False)]

    def update(self, dt, spawn=None):
        if self.state == "telegraph":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "extend"
        elif self.state == "extend":
            self.length = min(self.max_length, self.length + STRING_EXTEND_SPEED * dt)
            if self.length >= self.max_length:
                self.state = "hold"
                self.timer = STRING_HOLD_TIME
        elif self.state == "hold":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "retract"
        elif self.state == "retract":
            self.length = max(0.0, self.length - STRING_RETRACT_SPEED * dt)
            if self.length <= 0:
                self.dead = True
        # hitbox = the drawn rectangle (center-based: half a length below the anchor)
        box = self.hitboxes[0]
        box.height = self.length
        box.offset_y = self.length / 2
        box.enabled = self.state in ("extend", "hold", "retract") and self.length > 0

    def offscreen(self):
        return False   # anchored on its hand: it only expires

    def draw(self, surf):
        left = int(self.x - STRING_WIDTH / 2)
        if self.state == "telegraph":
            # blinking outline of the exact lane that is about to become dangerous
            if int(self.timer * 12) % 2 == 0:
                pygame.draw.rect(surf, WARNING, (left, int(self.y), STRING_WIDTH, int(self.max_length)), 3)
        else:
            pygame.draw.rect(surf, WHITE, (left, int(self.y), STRING_WIDTH, int(self.length)))
            pygame.draw.circle(surf, WARNING, (int(self.x), int(self.y + self.length)), STRING_WIDTH // 2)