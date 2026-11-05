import sys
import math
import pygame

# Config
WIDTH, HEIGHT = 960, 540
FPS = 60
DEBUG_KEYS = True  # 1/2/3 = jump to boss phase 1/2/3, G = toggle god mode

# Player Values
PLAYER_RADIUS = 14
PLAYER_SPEED = 320            # px/s

# Controller (button numbers differ between pads, adjust if yours is off)
JOY_DEADZONE = 0.2             # ignore stick values smaller than this
JOY_BTN_SHOOT = 0              # A on Xbox / Cross on PlayStation
JOY_BTN_RESTART = 7            # Start on Xbox
PLAYER_SHOOT_COOLDOWN = 0.1
PLAYER_BULLET_SPEED = 520
PLAYER_BULLET_RADIUS = 5

# Boss Values
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

# Attack: projectile rain (shell goes up, then splits into falling bullets)
RAIN_SHELL_SPEED = 420
RAIN_SHELL_RADIUS = 16
RAIN_SPLIT_Y = 60              # height where the shell splits
RAIN_COUNT = 7
RAIN_SPACING = 70              # horizontal gap between falling bullets
RAIN_SPEED = 250
RAIN_BULLET_RADIUS = 7

# Attack: sinusoidal projectile
WAVE_SPEED = 270
WAVE_RADIUS = 9
WAVE_AMPLITUDE = 90            # px, sideways swing around the straight path
WAVE_FREQ = 4.5                # rad/s

# Attack: big wall (covers 1/3 of the screen height)
WALL_WIDTH = 600
WALL_SPEED = 380
WALL_WARNING_TIME = 0.8        # lane is outlined before the wall becomes dangerous

# Colors Values
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
RED = (220, 60, 60)
ORANGE = (240, 150, 50)
CRIMSON = (150, 20, 60)
BLUE = (90, 160, 255)
PURPLE = (170, 90, 220)
GREEN = (90, 220, 120)
YELLOW = (240, 210, 90)
PINK = (240, 120, 200)
WARNING = (255, 120, 120)

# Boss phases. Each phase = a color, a movement speed and a SEQUENCE of
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


# Player Init
class Player:
    def __init__(self):
        self.x, self.y = 150, HEIGHT // 2
        self.alive = True
        self.shoot_timer = 0.0

    def update(self, dt, move_x, move_y, shooting, bullets):
        # move_x / move_y come from read_input(): -1..1, keyboard or controller
        self.x += move_x * PLAYER_SPEED * dt
        self.y += move_y * PLAYER_SPEED * dt
        self.x = max(PLAYER_RADIUS, min(WIDTH - PLAYER_RADIUS, self.x))
        self.y = max(PLAYER_RADIUS, min(HEIGHT - PLAYER_RADIUS, self.y))

        self.shoot_timer -= dt
        if shooting and self.shoot_timer <= 0:
            bullets.append(Bullet(self.x, self.y, PLAYER_BULLET_SPEED, 0, PLAYER_BULLET_RADIUS, BLUE))
            self.shoot_timer = PLAYER_SHOOT_COOLDOWN

    def draw(self, surf):
        pygame.draw.circle(surf, GREEN, (int(self.x), int(self.y)), PLAYER_RADIUS)


# Projectiles Init
# Every hazard (Bullet, RainShell, WaveBullet, Wall) offers the same 5 things:
# update(dt, spawn), offscreen(), hits(cx, cy, cr), draw(surf) and a `dead` flag.
# `spawn` is a list a hazard can append new hazards to (used by the rain).
class Bullet:
    def __init__(self, x, y, vx, vy, radius, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.radius = radius
        self.color = color
        self.dead = False

    def update(self, dt, spawn=None):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def offscreen(self):
        return self.x < -20 or self.x > WIDTH + 20 or self.y < -20 or self.y > HEIGHT + 20

    def hits(self, cx, cy, cr):
        return circle_hit(self.x, self.y, self.radius, cx, cy, cr)

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)


class RainShell(Bullet):
    """Large bullet that flies up, then splits into a row of falling bullets."""

    def __init__(self, x, y, vx, vy):
        super().__init__(x, y, vx, vy, RAIN_SHELL_RADIUS, YELLOW)

    def update(self, dt, spawn=None):
        super().update(dt)
        if self.y <= RAIN_SPLIT_Y:
            self.dead = True
            if spawn is not None:
                for i in range(RAIN_COUNT):
                    offset = (i - (RAIN_COUNT - 1) / 2) * RAIN_SPACING
                    spawn.append(Bullet(self.x + offset, RAIN_SPLIT_Y, 0, RAIN_SPEED,
                                        RAIN_BULLET_RADIUS, PURPLE))


class WaveBullet(Bullet):
    """Bullet that follows a straight path but swings sideways like a sine wave."""

    def __init__(self, x, y, angle):
        super().__init__(x, y, 0, 0, WAVE_RADIUS, PINK)
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


# Boss Init
class Boss:
    def __init__(self):
        self.x, self.y = BOSS_BASE_X, HEIGHT // 2
        self.hp = BOSS_MAX_HP
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
        ratio = self.hp / BOSS_MAX_HP
        if ratio > 2 / 3:
            return 1
        if ratio > 1 / 3:
            return 2
        return 3

    def invulnerable(self):
        return self.transition_timer > 0

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
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), BOSS_RADIUS)

        # minimal health bar (no UI), with a tick at each phase change
        ratio = max(self.hp, 0) / BOSS_MAX_HP
        bar_x = WIDTH // 2 - 150
        pygame.draw.rect(surf, BLACK, (bar_x - 2, 20, 304, 18))
        pygame.draw.rect(surf, color, (bar_x, 22, int(300 * ratio), 14))
        for tick in (1 / 3, 2 / 3):
            tx = bar_x + int(300 * tick)
            pygame.draw.line(surf, WHITE, (tx, 20), (tx, 38), 2)


def circle_hit(x1, y1, r1, x2, y2, r2):
    return math.hypot(x1 - x2, y1 - y2) < (r1 + r2)


def read_input(keys, joysticks):
    """Merge keyboard and controller(s) into (move_x, move_y, shooting)."""
    dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
    dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
    shooting = keys[pygame.K_SPACE]

    for joy in joysticks.values():
        # left stick, with a deadzone because sticks never rest at exactly 0
        jx, jy = joy.get_axis(0), joy.get_axis(1)
        if math.hypot(jx, jy) < JOY_DEADZONE:
            jx = jy = 0
        dx += jx
        dy += jy
        # D-pad (a "hat"): up is +1 on the hat but -y on screen
        if joy.get_numhats() > 0:
            hx, hy = joy.get_hat(0)
            dx += hx
            dy -= hy
        if joy.get_numbuttons() > JOY_BTN_SHOOT and joy.get_button(JOY_BTN_SHOOT):
            shooting = True

    # cap at length 1 so diagonals aren't faster; a half-pushed stick stays slower
    length = math.hypot(dx, dy)
    if length > 1:
        dx, dy = dx / length, dy / length
    return dx, dy, shooting


# Game Init
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Wandering in Whimsicave (prototype)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28)

    def new_game():
        return Player(), Boss(), [], [], "playing"

    player, boss, player_bullets, boss_bullets, state = new_game()
    god_mode = False

    # connected controllers, by instance id (so pads can be plugged in/out while playing)
    joysticks = {}
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joysticks[joy.get_instance_id()] = joy

    # debug: key -> boss HP fraction (just inside each phase)
    debug_phase_hp = {pygame.K_1: 1.0, pygame.K_2: 0.6, pygame.K_3: 0.3}

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                joysticks[joy.get_instance_id()] = joy
            if event.type == pygame.JOYDEVICEREMOVED:
                joysticks.pop(event.instance_id, None)
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == JOY_BTN_RESTART and state != "playing":
                    player, boss, player_bullets, boss_bullets, state = new_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r and state != "playing":
                    player, boss, player_bullets, boss_bullets, state = new_game()
                if DEBUG_KEYS and state == "playing":
                    if event.key in debug_phase_hp:
                        boss.hp = BOSS_MAX_HP * debug_phase_hp[event.key]
                    if event.key == pygame.K_g:
                        god_mode = not god_mode
                        print("God mode:", "ON" if god_mode else "OFF")

        keys = pygame.key.get_pressed()
        move_x, move_y, shooting = read_input(keys, joysticks)

        if state == "playing":
            player.update(dt, move_x, move_y, shooting, player_bullets)
            boss.update(dt, boss_bullets, player)

            for b in player_bullets:
                b.update(dt)

            # boss hazards can spawn new hazards (rain), so collect them first
            spawned = []
            for b in boss_bullets:
                b.update(dt, spawned)
            boss_bullets.extend(spawned)

            player_bullets[:] = [b for b in player_bullets if not b.offscreen()]
            boss_bullets[:] = [b for b in boss_bullets if not (b.dead or b.offscreen())]

            # collisions : Player vs. boss shots (absorbed, but no damage, during transitions)
            still_alive_bullets = []
            for b in player_bullets:
                if circle_hit(b.x, b.y, b.radius, boss.x, boss.y, BOSS_RADIUS):
                    boss.take_hit(1)
                else:
                    still_alive_bullets.append(b)
            player_bullets[:] = still_alive_bullets

            # collisions : boss hazards vs player
            if not god_mode:
                for b in boss_bullets:
                    if b.hits(player.x, player.y, PLAYER_RADIUS):
                        state = "lose"
                        break

            if boss.hp <= 0:
                state = "win"

        # Drawing
        screen.fill((25, 20, 35))
        boss.draw(screen)
        for b in boss_bullets:
            b.draw(screen)
        for b in player_bullets:
            b.draw(screen)
        player.draw(screen)

        if state == "win":
            txt = font.render("VICTOIRE ! Appuie sur R pour recommencer", True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 20))
        elif state == "lose":
            txt = font.render("TOUCHE... Appuie sur R pour reessayer", True, WHITE)
            screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 20))

        pygame.display.flip()


if __name__ == "__main__":
    main()