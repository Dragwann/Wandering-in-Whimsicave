import math

import pygame

from utilities.settings import WIDTH, HEIGHT, PINK, TEAL, WARNING
from utilities.hitbox import Hitbox
from utilities.placeholder import PlaceholderSprite
from utilities.attack_patterns import fire_pattern, pat

# Visuals. Drop a PNG at TWIN_*_IMAGE and it replaces the placeholder (hitbox stays as it is).
TWIN_TOP_IMAGE = "entities/Twin_top_asset.png"
TWIN_BOTTOM_IMAGE = "entities/Twin_bottom_asset.png"
TWIN_TOP_DRAW_HEIGHT = 120             # hauteur du sprite du haut (px), la largeur suit le ratio
TWIN_BOTTOM_DRAW_HEIGHT = 140          # hauteur du sprite du bas : à ajuster
TWIN_TOP_PLACEHOLDER_SIZE = (100, 120)
TWIN_BOTTOM_PLACEHOLDER_SIZE = (100, 140)
BACKGROUND_IMAGE = "backgrounds/Boss3_Miniboss1_background.png"
TWIN_BULLET_IMAGE = "projectiles/button.png"
TWIN_WAVE_IMAGE = "projectiles/yarn_ball.png"

# Twins values
TWINS_MAX_HP = 150                     # ONE pool for both puppets
TWIN_HITBOX_RADIUS = 42                # circle hitbox of EACH puppet, independent from the sprite
TWIN_TOP_Y = 75
TWIN_BOTTOM_Y = HEIGHT - 75
TWIN_CENTER_X = WIDTH // 2 + 40
TWIN_AMPLITUDE = 330                   # horizontal travel (px): the two puppets mirror each other
TWIN_MOVE_SPEED = 0.55                 # rad/s
TWIN_ENTER_TIME = 1.0                  # they slide in from the edges, invulnerable and silent
TWIN_ENTER_OFFSET = 160
TWIN_FIRST_ATTACK_DELAY = 0.8
TWIN_TELEGRAPH_TIME = 0.45             # the puppet about to shoot flashes and shows a ring
TWIN_ENRAGED_PACE = 0.8                # below 50% HP the waits are multiplied by this

# AIMED = {"type": "fan", "count": 1, "speed": 340, "radius": 13}
AIMED = {"type": "fan", "count": 1, "speed": 340, "radius": 13, "image": TWIN_BULLET_IMAGE}
WAVE = {"type": "wave", "count": 1, "image": TWIN_WAVE_IMAGE}
FAN = pat(AIMED, count=3, spread=36, speed=300)
# WAVE = {"type": "wave", "count": 1}

# (which puppet shoots: 0 = top, 1 = bottom, pattern, seconds before the NEXT attack). They alternate.
TWIN_SEQUENCE = [
    (0, AIMED, 0.9),
    (1, AIMED, 0.9),
    (0, FAN, 1.1),
    (1, FAN, 1.1),
    (0, WAVE, 0.5),
    (1, WAVE, 1.5),
    (0, pat(AIMED, speed=420), 0.35),    # "pincer": both shoot almost together
    (1, pat(AIMED, speed=420), 1.4),
]


class Puppet:
    """One of the two twins: a position, a hitbox and a sprite. The health lives in Twins."""

    def __init__(self, rest_y, image, draw_height, placeholder_size, color, label):
        self.rest_y = rest_y
        self.x, self.y = TWIN_CENTER_X, rest_y
        # Hitbox = the ONLY place where this puppet's collision size lives. Extra ones (weak points...)
        # can be appended to this list later.
        self.hitboxes = [Hitbox.circle(self, TWIN_HITBOX_RADIUS)]
        self.sprite = PlaceholderSprite(image, draw_height, placeholder_size, color, "rect", label)


class Twins:
    """Two puppets on opposite edges (top / bottom) sharing ONE health pool. They shoot alternately."""

    max_hp = TWINS_MAX_HP
    health_ticks = ()
    background_image = BACKGROUND_IMAGE

    def __init__(self):
        self.hp = self.max_hp
        self.puppets = [Puppet(TWIN_TOP_Y, TWIN_TOP_IMAGE, TWIN_TOP_DRAW_HEIGHT, TWIN_TOP_PLACEHOLDER_SIZE, PINK, "TWIN A"),
                Puppet(TWIN_BOTTOM_Y, TWIN_BOTTOM_IMAGE, TWIN_BOTTOM_DRAW_HEIGHT, TWIN_BOTTOM_PLACEHOLDER_SIZE, TEAL, "TWIN B")]
        self.enter_timer = TWIN_ENTER_TIME
        self.move_angle = 0.0
        self.step = 0
        self.attack_timer = TWIN_FIRST_ATTACK_DELAY
        self.place_puppets()

    # ---- interface shared by every boss / stage ----
    @property
    def hitboxes(self):
        """Both puppets' hitboxes: shooting either one hurts the same pool."""
        return [box for puppet in self.puppets for box in puppet.hitboxes]

    def invulnerable(self):
        return self.enter_timer > 0

    def deals_contact_damage(self):
        return not self.invulnerable()

    def take_hit(self, damage=1):
        if not self.invulnerable():
            self.hp -= damage

    def phase_color(self):
        return PINK

    def background_color(self):
        return (28, 20, 48)

    # ---- update ----
    def place_puppets(self):
        slide = max(0.0, self.enter_timer) / TWIN_ENTER_TIME * TWIN_ENTER_OFFSET   # 160 px -> 0 while entering
        wobble = math.sin(self.move_angle) * TWIN_AMPLITUDE
        top, bottom = self.puppets
        top.x, top.y = TWIN_CENTER_X + wobble, top.rest_y - slide
        bottom.x, bottom.y = TWIN_CENTER_X - wobble, bottom.rest_y + slide

    def update(self, dt, bullets, player):
        self.move_angle += dt * TWIN_MOVE_SPEED
        if self.enter_timer > 0:
            self.enter_timer -= dt
            self.place_puppets()
            return
        self.place_puppets()

        self.attack_timer -= dt
        if self.attack_timer <= 0:
            who, spec, wait = TWIN_SEQUENCE[self.step % len(TWIN_SEQUENCE)]
            puppet = self.puppets[who]
            fire_pattern(spec, puppet.x, puppet.y, player, bullets)
            pace = TWIN_ENRAGED_PACE if self.hp <= self.max_hp / 2 else 1.0
            self.attack_timer = wait * pace
            self.step += 1

    # ---- draw ----
    def draw_background(self, surf):
        pass   # the encounter draws the background

    def draw(self, surf):
        next_who = TWIN_SEQUENCE[self.step % len(TWIN_SEQUENCE)][0]
        telegraphing = self.enter_timer <= 0 and self.attack_timer <= TWIN_TELEGRAPH_TIME
        for i, puppet in enumerate(self.puppets):
            warn = telegraphing and i == next_who
            blink = self.enter_timer > 0 and int(self.enter_timer * 10) % 2 == 0
            puppet.sprite.draw(surf, puppet.x, puppet.y, flash=warn and int(self.attack_timer * 20) % 2 == 0 or blink)
            if warn:
                pygame.draw.circle(surf, WARNING, (int(puppet.x), int(puppet.y)),
                                   TWIN_HITBOX_RADIUS + 14, 3)