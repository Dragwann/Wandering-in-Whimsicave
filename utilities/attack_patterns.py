"""Reusable attack patterns for the Boss 3 encounter (Twins, Reflection and Puppeteer).

A pattern is a plain dict. fire_pattern(spec, x, y, player, bullets) builds the projectiles with
the EXISTING projectile / hazard classes and appends them to `bullets` (the boss_bullets list).
(x, y) is where the attacker is. Adding a pattern type = one function + one line in PATTERNS.

Keys by type (everything has a default except "type"):

  "fan"      count, spread (deg, total), speed, aim ("player" or a fixed angle in deg: 180 = left),
             angle_offset (deg)
  "ring"     count, speed, spawn_radius (px), rotation (deg),
             center ("origin" or "player"), inward (True = bullets fly to the center)
  "curtain"  a vertical line of bullets flying left, with a hole in it:
             spacing (px), gap (0..1 of the screen height, or "player"), gap_size (px), speed
  "rain"     x ("player" or 0..1 of the screen width): a shell flies up, then splits (RainShell)
  "wave"     count, spread (deg): sinusoidal bullets (WaveBullet)
  "wall"     lane (0 top / 1 middle / 2 bottom)
  "mine"     at ("player", "origin" or (fx, fy) fractions of the screen)

Bullet keys (fan, ring, curtain): radius (HITBOX radius, the placeholder circle uses it too),
  color, image (asset path, optional: the sprite is separate from the hitbox),
  hold  = seconds the bullet stays still before flying,
  arm   = seconds the bullet is a harmless ghost before it can hurt.

Sequence keys (used by the Puppeteer runner, ignored here): delay = activation delay of the pattern.
"""
import math

from utilities.settings import WIDTH, HEIGHT, PURPLE, PINK, ORANGE
from utilities.placeholder import optional_image
from projectiles.projectiles import (Bullet, DelayedBullet, RainShell, WaveBullet,
                                     RAIN_SPLIT_Y, RAIN_SHELL_SPEED)
from projectiles.hazards import Wall, Mine

DEFAULT_RADIUS = 12
DEFAULT_IMAGE_HEIGHT = 36      # on-screen height of a bullet sprite, when a spec gives an "image"


def pat(base, **overrides):
    """Copy of a pattern with some keys changed: pat(FAN, count=5, delay=0.4)."""
    return {**base, **overrides}


# ---------------------------------------------------------------- helpers

def _bullet(x, y, vx, vy, spec, default_color):
    radius = spec.get("radius", DEFAULT_RADIUS)
    color = spec.get("color", default_color)
    image = optional_image(spec.get("image"), height=spec.get("image_height", DEFAULT_IMAGE_HEIGHT))
    hold, arm = spec.get("hold", 0.0), spec.get("arm", 0.0)
    if hold > 0 or arm > 0:
        return DelayedBullet(x, y, vx, vy, radius, color, image, hold, arm)
    return Bullet(x, y, vx, vy, radius, color, image)


def _aim_angle(spec, x, y, player):
    aim = spec.get("aim", "player")
    base = math.atan2(player.y - y, player.x - x) if aim == "player" else math.radians(aim)
    return base + math.radians(spec.get("angle_offset", 0.0))


# ---------------------------------------------------------------- patterns

def fire_fan(spec, x, y, player, bullets):
    count = spec.get("count", 1)
    spread = math.radians(spec.get("spread", 0.0))
    speed = spec.get("speed", 300)
    base = _aim_angle(spec, x, y, player)
    for i in range(count):
        t = 0.0 if count == 1 else i / (count - 1) - 0.5
        a = base + spread * t
        bullets.append(_bullet(x, y, math.cos(a) * speed, math.sin(a) * speed, spec, PURPLE))


def fire_ring(spec, x, y, player, bullets):
    count = spec.get("count", 12)
    speed = spec.get("speed", 230)
    spawn_radius = spec.get("spawn_radius", 0)
    inward = spec.get("inward", False)
    cx, cy = (player.x, player.y) if spec.get("center", "origin") == "player" else (x, y)
    start = math.radians(spec.get("rotation", 0.0))
    sign = -1 if inward else 1
    for i in range(count):
        a = start + 2 * math.pi * i / count
        dx, dy = math.cos(a), math.sin(a)
        bx, by = cx + dx * spawn_radius, cy + dy * spawn_radius
        if not (0 <= bx <= WIDTH and 0 <= by <= HEIGHT):
            continue   # a bullet that would appear off screen is simply not created
        bullets.append(_bullet(bx, by, sign * dx * speed, sign * dy * speed, spec, PINK))


def fire_curtain(spec, x, y, player, bullets):
    spacing = spec.get("spacing", 46)
    gap = spec.get("gap", 0.5)
    gap_y = player.y if gap == "player" else gap * HEIGHT
    half_gap = spec.get("gap_size", 150) / 2
    speed = spec.get("speed", 190)
    row_y = spacing / 2
    while row_y < HEIGHT:
        if abs(row_y - gap_y) >= half_gap:
            bullets.append(_bullet(x, row_y, -speed, 0, spec, ORANGE))
        row_y += spacing


def fire_rain(spec, x, y, player, bullets):
    fx = spec.get("x", "player")
    target_x = player.x if fx == "player" else fx * WIDTH
    target_x = max(60, min(WIDTH - 60, target_x))
    angle = math.atan2(RAIN_SPLIT_Y - y, target_x - x)
    bullets.append(RainShell(x, y, math.cos(angle) * RAIN_SHELL_SPEED, math.sin(angle) * RAIN_SHELL_SPEED,
                             spec.get("image"), spec.get("image_height")))


def fire_wave(spec, x, y, player, bullets):
    count = spec.get("count", 1)
    spread = math.radians(spec.get("spread", 0.0))
    base = _aim_angle(spec, x, y, player)
    for i in range(count):
        t = 0.0 if count == 1 else i / (count - 1) - 0.5
        bullets.append(WaveBullet(x, y, base + spread * t, spec.get("image"), spec.get("image_height")))


def fire_wall(spec, x, y, player, bullets):
    bullets.append(Wall(spec.get("lane", 1), spec.get("image")))


def fire_mine(spec, x, y, player, bullets):
    at = spec.get("at", "player")
    if at == "player":
        mx, my = player.x, player.y
    elif at == "origin":
        mx, my = x, y
    else:
        mx, my = at[0] * WIDTH, at[1] * HEIGHT
    bullets.append(Mine(mx, my, spec.get("image"), spec.get("image_height")))


PATTERNS = {
    "fan": fire_fan,
    "ring": fire_ring,
    "curtain": fire_curtain,
    "rain": fire_rain,
    "wave": fire_wave,
    "wall": fire_wall,
    "mine": fire_mine,
}


def fire_pattern(spec, x, y, player, bullets):
    """Spawn one pattern. An unknown "type" raises KeyError on purpose (typo = loud error)."""
    PATTERNS[spec["type"]](spec, x, y, player, bullets)