import math
import random
import pygame

from utilities.settings import WIDTH, HEIGHT, WHITE, WARNING, RED, YELLOW, TEAL, SHOW_HITBOXES
from projectiles.projectiles import TrailBullet, TRAIL_INTERVAL
from projectiles.hazards import Mine
from utilities.utils import load_image, white_silhouette, soften_background

BOSS_IMAGE = "entities/Boss2_asset.png"
BOSS_DRAW_HEIGHT = 330
BACKGROUND_IMAGE = "backgrounds/Boss2_background.jpg"
BACKGROUND_DIM = 0.45
BACKGROUND_TINT = (15, 10, 30)
BACKGROUND_BLUR = 3

# Boss 2 Values
BOSS2_RADIUS = 40
BOSS2_MAX_HP = 300
BOSS2_BASE_X = WIDTH - 130
BOSS2_FIRST_ATTACK_DELAY = 1.0 # pause before the first action of a phase
BOSS2_TRANSITION_TIME = 1.0    # short invulnerability between phases
BOSS2_MARGIN = 60              # the boss stays this far from the screen edges
BOSS2_MOVE_SPEED = 420         # px/s, repositioning and wandering
BOSS2_DASH_SPEED = 800         # px/s
BOSS2_TELEGRAPH_TIME = 0.6     # warning before each dash
BOSS2_RECOVER_TIME = 0.5       # pause after each dash

# Boss 2 phases. Each phase says WHICH mechanics are on, and how fast.
# speed_mult multiplies every speed and divides every wait (= faster pacing).
BOSS2_PHASES = {
    1: {"color": TEAL,   "dash": True,  "mines": False, "mine_interval": 0.0, "speed_mult": 1.0},
    2: {"color": YELLOW, "dash": False, "mines": True,  "mine_interval": 1.3, "speed_mult": 1.0},
    3: {"color": RED,    "dash": True,  "mines": True,  "mine_interval": 1.0, "speed_mult": 1.35},
}


class Boss2:
    """Fast boss. Phase 1: dashes + trail. Phase 2: wanders + drops mines. Phase 3: both, faster.

    Movement is TARGET-BASED: the boss picks a point, walks toward it at a fixed speed,
    and picks a new one on arrival. No teleporting, ever.

    In dash phases it runs a small state machine:
        reposition -> telegraph -> dash -> recover -> reposition -> ...
    """

    def __init__(self):
        self.x, self.y = BOSS2_BASE_X, HEIGHT // 2
        self.radius = BOSS2_RADIUS
        self.max_hp = BOSS2_MAX_HP
        self.hp = self.max_hp
        self.phase = 1
        self.transition_timer = 0.0
        self.reset_behavior()
        # images (the pygame window must already exist when a Boss2 is created)
        self.image = load_image(BOSS_IMAGE, height=BOSS_DRAW_HEIGHT)
        self.flash_image = white_silhouette(self.image)   # white copy, used for blinks
        self.image_flipped = pygame.transform.flip(self.image, True, False)
        self.flash_flipped = pygame.transform.flip(self.flash_image, True, False)
        self.facing_right = False
        self.background = soften_background(
            load_image(BACKGROUND_IMAGE, size=(WIDTH, HEIGHT), alpha=False),
            BACKGROUND_DIM, BACKGROUND_TINT, BACKGROUND_BLUR)

    # ---- HP / phases ----
    def get_phase(self):
        ratio = self.hp / self.max_hp
        if ratio > 2 / 3:
            return 1
        if ratio > 1 / 3:
            return 2
        return 3

    def invulnerable(self):
        return self.transition_timer > 0

    def deals_contact_damage(self):
        return not self.invulnerable()   # touching it hurts, except during a phase change

    def take_hit(self, damage=1):
        if not self.invulnerable():
            self.hp -= damage

    def start_phase(self, new_phase, bullets):
        self.phase = new_phase
        self.transition_timer = BOSS2_TRANSITION_TIME
        bullets.clear()   # clean slate (trail + mines) so the player can breathe
        self.reset_behavior()

    def reset_behavior(self):
        """Called at spawn and at every phase change."""
        cfg = BOSS2_PHASES[self.phase]
        self.state = "recover" if cfg["dash"] else "wander"
        self.state_timer = BOSS2_FIRST_ATTACK_DELAY
        self.mine_timer = BOSS2_FIRST_ATTACK_DELAY
        self.trail_timer = 0.0
        self.dash_target = (self.x, self.y)
        self.start_point = (self.x, self.y)
        self.target = (self.x, self.y)
        self.pick_wander_target()

    # ---- Movement helpers ----
    def move_toward(self, target, speed, dt):
        """Move at `speed` toward target. Returns True once the target is reached."""
        tx, ty = target
        dx, dy = tx - self.x, ty - self.y
        if abs(dx) > 5:                      # seuil pour ne pas changer de sens sur un mouvement presque vertical
            self.facing_right = dx > 0
        dist = math.hypot(dx, dy)
        step = speed * dt
        if dist <= step:
            self.x, self.y = tx, ty
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        return False

    def pick_wander_target(self):
        m = BOSS2_MARGIN
        for _ in range(10):   # retry so the boss never picks a point right next to itself
            tx = random.uniform(m, WIDTH - m)
            ty = random.uniform(m, HEIGHT - m)
            if math.hypot(tx - self.x, ty - self.y) > 250:
                break
        self.target = (tx, ty)

    def pick_dash_start(self):
        """Choose an edge point to start from (horizontal or vertical dash)."""
        m = BOSS2_MARGIN
        if random.random() < 0.6:
            self.dash_axis = "h"
            sx = random.choice([m, WIDTH - m])
            sy = random.uniform(m, HEIGHT - m)
        else:
            self.dash_axis = "v"
            sx = random.uniform(m, WIDTH - m)
            sy = random.choice([m, HEIGHT - m])
        self.start_point = (sx, sy)

    def begin_telegraph(self, player, mult):
        """Lock the dash target NOW: the player sees the line and has time to react."""
        m = BOSS2_MARGIN
        sx, sy = self.start_point
        if self.dash_axis == "h":
            self.dash_target = (WIDTH - sx, max(m, min(HEIGHT - m, player.y)))
        else:
            self.dash_target = (max(m, min(WIDTH - m, player.x)), HEIGHT - sy)
        self.state = "telegraph"
        self.state_timer = BOSS2_TELEGRAPH_TIME / mult

    # ---- Update ----
    def update(self, dt, bullets, player):
        if self.get_phase() != self.phase:
            self.start_phase(self.get_phase(), bullets)

        # Transition: invulnerable, frozen, silent
        if self.transition_timer > 0:
            self.transition_timer -= dt
            return

        cfg = BOSS2_PHASES[self.phase]
        mult = cfg["speed_mult"]

        # Mines: an independent timer, active in phases 2 and 3 whatever the boss is doing
        if cfg["mines"]:
            self.mine_timer -= dt
            if self.mine_timer <= 0:
                bullets.append(Mine(self.x, self.y))
                self.mine_timer = cfg["mine_interval"]

        if cfg["dash"]:
            self.update_dash(dt, bullets, player, mult)
        else:
            self.update_wander(dt, mult)

    def update_wander(self, dt, mult):
        if self.move_toward(self.target, BOSS2_MOVE_SPEED * mult, dt):
            self.pick_wander_target()

    def update_dash(self, dt, bullets, player, mult):
        if self.state == "reposition":
            if self.move_toward(self.start_point, BOSS2_MOVE_SPEED * mult, dt):
                self.begin_telegraph(player, mult)

        elif self.state == "telegraph":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "dash"
                self.trail_timer = 0.0

        elif self.state == "dash":
            # leave a trail bullet behind, then move
            self.trail_timer -= dt
            if self.trail_timer <= 0:
                bullets.append(TrailBullet(self.x, self.y))
                self.trail_timer = TRAIL_INTERVAL
            if self.move_toward(self.dash_target, BOSS2_DASH_SPEED * mult, dt):
                self.state = "recover"
                self.state_timer = BOSS2_RECOVER_TIME / mult

        elif self.state == "recover":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.pick_dash_start()
                self.state = "reposition"

    # ---- Draw ----
    def draw_background(self, surf):
        surf.blit(self.background, (0, 0))

    def draw(self, surf):
        color = BOSS2_PHASES[self.phase]["color"]
        flash = self.invulnerable() and int(self.transition_timer * 10) % 2 == 0
        if self.state == "telegraph":
            # the line shows exactly where the dash will go
            pygame.draw.line(surf, WARNING, (int(self.x), int(self.y)),
                             (int(self.dash_target[0]), int(self.dash_target[1])), 3)
            pygame.draw.circle(surf, WARNING, (int(self.dash_target[0]), int(self.dash_target[1])),
                               self.radius, 2)
            if int(self.state_timer * 20) % 2 == 0:
                flash = True
        if flash:
            color = WHITE   # the health bar blinks too, like before

        if self.facing_right:
            img = self.flash_flipped if flash else self.image_flipped
        else:
            img = self.flash_image if flash else self.image
        surf.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
        if SHOW_HITBOXES:
            pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.radius, 1)