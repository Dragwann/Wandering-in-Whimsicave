import math
import pygame

from utilities.settings import WIDTH, HEIGHT, WHITE, RED, ORANGE, CRIMSON, PURPLE
from projectiles.projectiles import Bullet, RainShell, WaveBullet, RAIN_SPLIT_Y, RAIN_SHELL_SPEED
from projectiles.hazards import Wall
from utilities.ui import draw_health_bar

# Boss 1 Values
BOSS_RADIUS = 55
BOSS_MAX_HP = 300
BOSS_BASE_X = WIDTH - 130
BOSS_MOVE_RANGE = 170          # vertical amplitude (px)
BOSS_SWAY = 12                 # tiny horizontal movement (px)
PHASE_TRANSITION_TIME = 1.5    # boss is invulnerable and silent during this time
FIRST_ATTACK_DELAY = 1.0       # pause before the first attack of a phase

# Attack: direct shot
DIRECT_SPEED = 300
DIRECT_RADIUS = 8

# Boss 1 phases. Each phase = a color, a movement speed and a SEQUENCE of
# (attack_name, delay_in_seconds_after_this_attack). The boss loops over it.
# Phase 1 : HP > 66%        -> direct shots + rain
# Phase 2 : 33% < HP <= 66% -> adds the sinusoidal projectile
# Phase 3 : HP <= 33%       -> adds the big wall, faster pacing
# Rule for phase 3: keep walls spaced enough so that at most 2 are on screen
# at once, otherwise there is no safe lane left.
PHASES = {
    1: {
        "color": RED,
        "move_speed": 0.7,
        "sequence": [("direct", 1.0), ("direct", 1.0), ("direct", 1.0), ("rain", 2.2)],
    },
    2: {
        "color": ORANGE,
        "move_speed": 0.8,
        "sequence": [("direct", 0.8), ("wave", 1.3), ("direct", 0.8), ("wave", 1.3), ("rain", 2.0)],
    },
    3: {
        "color": CRIMSON,
        "move_speed": 0.9,
        "sequence": [("wall", 1.2), ("direct", 0.7), ("wall", 1.2), ("wave", 0.8), ("rain", 2.2)],
    },
}


class Boss:
    def __init__(self):
        self.x, self.y = BOSS_BASE_X, HEIGHT // 2
        self.radius = BOSS_RADIUS
        self.max_hp = BOSS_MAX_HP
        self.hp = self.max_hp
        self.phase = 1
        self.move_angle = 0.0
        self.transition_timer = 0.0
        self.attack_index = 0                 # position in the current phase sequence
        self.attack_timer = FIRST_ATTACK_DELAY
        self.wall_index = 0                   # walls go top -> middle -> bottom -> ...
        # attack name (used in PHASES) -> method
        self.attacks = {
            "direct": self.attack_direct,
            "rain": self.attack_rain,
            "wave": self.attack_wave,
            "wall": self.attack_wall,
        }

    # ---- HP / phases ----
    def get_phase(self):
        """Phase depends on the fraction of HP left."""
        ratio = self.hp / self.max_hp
        if ratio > 2 / 3:
            return 1
        if ratio > 1 / 3:
            return 2
        return 3

    def invulnerable(self):
        return self.transition_timer > 0

    def deals_contact_damage(self):
        return False   # Boss 1 is harmless to touch

    def take_hit(self, damage=1):
        if not self.invulnerable():
            self.hp -= damage

    def start_phase(self, new_phase, bullets):
        self.phase = new_phase
        self.transition_timer = PHASE_TRANSITION_TIME
        self.attack_index = 0
        self.attack_timer = FIRST_ATTACK_DELAY
        bullets.clear()   # clean slate so the player can breathe

    # ---- Update ----
    def update(self, dt, bullets, player):
        if self.get_phase() != self.phase:
            self.start_phase(self.get_phase(), bullets)

        cfg = PHASES[self.phase]

        # Movement: slow vertical sine, tiny horizontal sway (fully predictable)
        self.move_angle += dt * cfg["move_speed"]
        self.y = HEIGHT // 2 + math.sin(self.move_angle) * BOSS_MOVE_RANGE
        self.x = BOSS_BASE_X + math.sin(self.move_angle * 0.5) * BOSS_SWAY

        # Transition: invulnerable, no attacks
        if self.transition_timer > 0:
            self.transition_timer -= dt
            return

        # Attacks: run the sequence of the current phase, one attack at a time
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            name, delay = cfg["sequence"][self.attack_index]
            self.attacks[name](bullets, player)
            self.attack_timer = delay
            self.attack_index = (self.attack_index + 1) % len(cfg["sequence"])

    # ---- Attacks (all share the same signature) ----
    def attack_direct(self, bullets, player):
        angle = math.atan2(player.y - self.y, player.x - self.x)
        bullets.append(Bullet(self.x, self.y,
                              math.cos(angle) * DIRECT_SPEED, math.sin(angle) * DIRECT_SPEED,
                              DIRECT_RADIUS, PURPLE))

    def attack_rain(self, bullets, player):
        # shell flies toward the top of the screen, above where the player is now
        target_x = max(60, min(WIDTH - 60, player.x))
        angle = math.atan2(RAIN_SPLIT_Y - self.y, target_x - self.x)
        bullets.append(RainShell(self.x, self.y,
                                 math.cos(angle) * RAIN_SHELL_SPEED, math.sin(angle) * RAIN_SHELL_SPEED))

    def attack_wave(self, bullets, player):
        angle = math.atan2(player.y - self.y, player.x - self.x)
        bullets.append(WaveBullet(self.x, self.y, angle))

    def attack_wall(self, bullets, player):
        bullets.append(Wall(self.wall_index % 3))
        self.wall_index += 1

    # ---- Draw ----
    def draw(self, surf):
        color = PHASES[self.phase]["color"]
        # Flash white during the transition so the player understands something changed
        if self.invulnerable() and int(self.transition_timer * 10) % 2 == 0:
            color = WHITE
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), self.radius)
        draw_health_bar(surf, self.hp, self.max_hp, color)
