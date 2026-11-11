import math

from utilities.settings import WIDTH, HEIGHT, WHITE, PURPLE, PINK, CRIMSON, YELLOW, ORANGE
from utilities.hitbox import Hitbox
from utilities.placeholder import PlaceholderSprite
from utilities.attack_patterns import fire_pattern, pat

# Visuals (drop a PNG at PUPPETEER_IMAGE to replace the placeholder; the hitbox does not change)
PUPPETEER_IMAGE = "entities/Puppeteer_asset.png"
PUPPETEER_DRAW_HEIGHT = 300
PUPPETEER_PLACEHOLDER_SIZE = (180, 300)

# Puppeteer values
PUPPETEER_MAX_HP = 500                  # ONE pool for the 3 phases, never reset
PUPPETEER_HITBOX_RADIUS = 80            # circle hitbox, independent from the sprite size
PUPPETEER_BASE_X = WIDTH - 130
PUPPETEER_TRANSITION_TIME = 1.2         # invulnerable and silent between phases
PUPPETEER_FIRST_ATTACK_DELAY = 1.0      # pause before the first step of a phase
INTERRUPT_FLASH_TIME = 0.3              # the boss blinks white when it cuts its own sequence

# ---- attack building blocks (see attack_patterns.py for every key) ----
AIMED = {"type": "fan", "count": 1, "speed": 340, "radius": 13, "color": PURPLE}
FAN = pat(AIMED, count=3, spread=30, speed=310, radius=12)
# bullets appear in a ring around the boss, stay still for 0.6 s (hold), then fly outward
BURST = {"type": "ring", "count": 12, "speed": 230, "spawn_radius": 110, "hold": 0.6, "radius": 11, "color": PINK}
# bullets appear around the PLAYER, wait, then all fly toward the spot where the player was
CLOSING = {"type": "ring", "count": 10, "speed": 250, "center": "player", "spawn_radius": 190,
           "inward": True, "hold": 0.9, "radius": 11, "color": ORANGE}
# a vertical line of bullets with a hole in it; ghosts (arm) and still (hold) for 0.7 s so the hole can be read
CURTAIN = {"type": "curtain", "spacing": 46, "gap": 0.5, "gap_size": 150, "speed": 190,
           "hold": 0.7, "arm": 0.7, "radius": 14, "color": YELLOW}
RAIN = {"type": "rain"}
WAVE = {"type": "wave", "count": 1}
MINE = {"type": "mine", "at": "player"}
WALL = {"type": "wall", "lane": 1}

# ---- phases ----
# "sequence": list of steps (patterns, wait). All the patterns of a step are queued together; a pattern
#   with "delay" fires that many seconds after the step starts. `wait` = seconds before the next step.
#   A phase loops over its sequence.
# "interrupts": predefined opportunities to CUT the sequence:
#   step / after  = when: `after` seconds after step `step` started
#   cooldown      = minimum time between two uses (the first use is also `cooldown` seconds into the phase)
#   attack        = (patterns, wait), played instead of what the sequence had left to do
#   resume        = "restart" (back to step 0) or "next" (continue after the interrupted step)
#   Cutting only cancels what was still PENDING. Bullets already in the air are never touched.
# tempo divides every wait and delay; move_* describe the movement (see move()).
PHASES = {
    1: {   # The Test: familiar attacks, in an unexpected order
        "color": PURPLE, "tempo": 1.0,
        "move_speed": 0.7, "move_range": 160, "sway": 20, "harmonic": 0.0,
        "sequence": [
            ([AIMED], 1.0),
            ([AIMED, pat(AIMED, delay=0.35)], 1.4),                       # double tap
            ([RAIN], 1.8),
            ([BURST], 1.6),
            ([FAN, pat(FAN, delay=0.6)], 1.8),
        ],
        "interrupts": [
            {"step": 1, "after": 0.2, "cooldown": 9.0, "resume": "restart",
             "attack": ([pat(FAN, count=7, spread=84, speed=300, delay=0.3)], 1.6)},
            {"step": 4, "after": 0.3, "cooldown": 12.0, "resume": "next",
             "attack": ([pat(CLOSING, delay=0.2)], 2.2)},
        ],
    },
    2: {   # Pressure: denser, faster, more delayed bullets
        "color": PINK, "tempo": 1.15,
        "move_speed": 0.8, "move_range": 160, "sway": 45, "harmonic": 0.15,
        "sequence": [
            ([FAN, pat(AIMED, delay=0.3), pat(AIMED, delay=0.6)], 1.0),
            ([pat(CURTAIN, gap=0.25)], 1.5),
            ([RAIN, pat(FAN, delay=0.7)], 1.5),
            ([pat(BURST, count=14), pat(MINE, delay=0.2)], 1.4),
            ([CLOSING, pat(AIMED, delay=1.0)], 1.6),
            ([pat(CURTAIN, gap=0.75), pat(WAVE, delay=0.5)], 1.6),
        ],
        "interrupts": [
            {"step": 0, "after": 0.35, "cooldown": 7.0, "resume": "restart",
             "attack": ([pat(FAN, count=9, spread=100, speed=300, delay=0.3), pat(MINE, delay=0.7)], 1.4)},
            {"step": 3, "after": 0.4, "cooldown": 10.0, "resume": "next",
             "attack": ([pat(CURTAIN, gap=0.5, gap_size=140, delay=0.25), pat(AIMED, delay=0.9)], 1.6)},
        ],
    },
    3: {   # Chaos: the nastiest patterns, with a changing rhythm (fast / slow steps)
        "color": CRIMSON, "tempo": 1.25,
        "move_speed": 0.95, "move_range": 165, "sway": 90, "harmonic": 0.35,
        "sequence": [
            ([pat(CURTAIN, gap=0.7, gap_size=130, speed=230), pat(AIMED, delay=0.9)], 1.2),
            ([pat(CURTAIN, gap=0.25, gap_size=130, speed=230)], 1.6),
            ([WALL, pat(FAN, count=5, spread=50, speed=300, delay=0.6)], 1.4),
            ([pat(BURST, count=16, spawn_radius=140), pat(CLOSING, delay=0.6)], 1.8),
            ([pat(WAVE, count=3, spread=40), pat(RAIN, delay=0.5)], 1.2),
            ([pat(WALL, lane=0), pat(WALL, lane=2), pat(AIMED, delay=1.0)], 2.2),
        ],
        "interrupts": [
            {"step": 0, "after": 0.5, "cooldown": 6.0, "resume": "restart",
             "attack": ([pat(FAN, count=7, spread=70, speed=320, delay=0.25), pat(MINE, delay=0.6),
                         pat(FAN, count=7, spread=70, speed=320, delay=1.0)], 1.5)},
            {"step": 3, "after": 0.3, "cooldown": 8.0, "resume": "next",
             "attack": ([pat(WALL, lane=1, delay=0.2), pat(CLOSING, count=12, delay=0.5)], 1.8)},
            {"step": 4, "after": 0.4, "cooldown": 10.0, "resume": "restart",
             "attack": ([pat(BURST, count=20, spawn_radius=160, hold=0.8, delay=0.3)], 1.6)},
        ],
    },
}


def _validate_phases():
    """Catches typos in the data at import time: an interrupt must point at a real step, and must be
    able to happen before that step ends."""
    for number, cfg in PHASES.items():
        sequence = cfg["sequence"]
        for it in cfg["interrupts"]:
            assert 0 <= it["step"] < len(sequence), f"phase {number}: unknown step {it['step']}"
            assert it["after"] < sequence[it["step"]][1] / cfg["tempo"], \
                f"phase {number}: interrupt after {it['after']} s can never happen in step {it['step']}"
            assert it["resume"] in ("restart", "next")


_validate_phases()


class Puppeteer:
    """Final boss. One entity, three phases (HP thresholds like Boss 1 / Boss 2, HP never reset).

    Attacks: the phase's sequence runs step after step. Each step queues its patterns in
    `self.pending` (pattern, time left). An interruption empties `pending` and queues its own attack:
    only the actions not fired yet are lost.
    """

    max_hp = PUPPETEER_MAX_HP
    health_ticks = (1 / 3, 2 / 3)

    def __init__(self, hitbox_radius=PUPPETEER_HITBOX_RADIUS):
        self.x, self.y = PUPPETEER_BASE_X, HEIGHT // 2
        self.hp = self.max_hp
        self.phase = 1
        self.move_angle = 0.0
        self.transition_timer = 0.0
        self.flash_timer = 0.0
        self.interrupt_count = 0            # how many times a sequence was cut (debug / tests)
        # Hitbox = the ONLY place where the boss's collision size lives (add weak points to this list).
        self.hitboxes = [Hitbox.circle(self, hitbox_radius)]
        self.sprite = PlaceholderSprite(PUPPETEER_IMAGE, PUPPETEER_DRAW_HEIGHT, PUPPETEER_PLACEHOLDER_SIZE,
                                        PURPLE, "ellipse", "PUPPETEER")
        self.reset_sequence()

    # ---- HP / phases ----
    def get_phase(self):
        ratio = self.hp / self.max_hp
        if ratio > 2 / 3:
            return 1
        if ratio > 1 / 3:
            return 2
        return 3

    def phase_color(self):
        return WHITE if self.flashing() else PHASES[self.phase]["color"]

    def background_color(self):
        # fantasy -> apocalypse: placeholder tint per phase (replace by real backgrounds later)
        return {1: (40, 16, 34), 2: (62, 14, 28), 3: (92, 8, 14)}[self.phase]

    def flashing(self):
        blinking = self.invulnerable() or self.flash_timer > 0
        timer = self.transition_timer if self.invulnerable() else self.flash_timer
        return blinking and int(timer * 10) % 2 == 0

    def invulnerable(self):
        return self.transition_timer > 0

    def deals_contact_damage(self):
        return not self.invulnerable()

    def take_hit(self, damage=1):
        if not self.invulnerable():
            self.hp -= damage

    def start_phase(self, new_phase, bullets):
        self.phase = new_phase
        self.transition_timer = PUPPETEER_TRANSITION_TIME
        bullets.clear()   # clean slate so the player can breathe (same convention as Boss 1 / Boss 2)
        self.reset_sequence()

    # ---- sequence runner ----
    def reset_sequence(self):
        cfg = PHASES[self.phase]
        self.step_index = 0                 # next step to start
        self.step_timer = PUPPETEER_FIRST_ATTACK_DELAY
        self.step_elapsed = 0.0             # time since the current step started
        self.current_step = None            # step in progress (None = right after an interruption)
        self.pending = []                   # [time_left, pattern] still to fire
        self.interrupt_cooldowns = [it["cooldown"] for it in cfg["interrupts"]]

    def start_step(self, cfg):
        specs, wait = cfg["sequence"][self.step_index]
        for spec in specs:
            self.pending.append([spec.get("delay", 0.0) / cfg["tempo"], spec])
        self.current_step = self.step_index
        self.step_elapsed = 0.0
        self.step_timer = wait / cfg["tempo"]
        self.step_index = (self.step_index + 1) % len(cfg["sequence"])

    def interrupt(self, n, cfg):
        it = cfg["interrupts"][n]
        self.interrupt_count += 1
        self.interrupt_cooldowns[n] = it["cooldown"]
        self.pending = []                   # cancel what the sequence still had to do (bullets in the air stay)
        specs, wait = it["attack"]
        for spec in specs:
            self.pending.append([spec.get("delay", 0.0) / cfg["tempo"], spec])
        self.step_timer = wait / cfg["tempo"]
        self.step_index = 0 if it["resume"] == "restart" else (it["step"] + 1) % len(cfg["sequence"])
        self.current_step = None            # an interruption can not be interrupted
        self.flash_timer = INTERRUPT_FLASH_TIME

    def run_sequence(self, dt, cfg, bullets, player):
        self.interrupt_cooldowns = [max(0.0, c - dt) for c in self.interrupt_cooldowns]

        # 1) interruption opportunities (only while a step is in progress, and only if the cooldown allows)
        if self.current_step is not None:
            self.step_elapsed += dt
            for n, it in enumerate(cfg["interrupts"]):
                if (it["step"] == self.current_step and self.step_elapsed >= it["after"]
                        and self.interrupt_cooldowns[n] <= 0):
                    self.interrupt(n, cfg)
                    break

        # 2) next step of the sequence
        self.step_timer -= dt
        if self.step_timer <= 0:
            self.start_step(cfg)

        # 3) fire the patterns whose activation delay is over
        still_waiting = []
        for item in self.pending:
            item[0] -= dt
            if item[0] <= 0:
                fire_pattern(item[1], self.x, self.y, player, bullets)
            else:
                still_waiting.append(item)
        self.pending = still_waiting

    # ---- movement ----
    def move(self, dt, cfg):
        """Vertical slow sine (+ a faster harmonic in the late phases) and a horizontal sway,
        so the shots come from varying angles. Always on the right side."""
        self.move_angle += dt * cfg["move_speed"]
        a, h = self.move_angle, cfg["harmonic"]
        self.y = HEIGHT // 2 + (math.sin(a) * (1 - h) + math.sin(a * 2.3) * h) * cfg["move_range"]
        self.x = PUPPETEER_BASE_X + math.sin(a * 0.5) * cfg["sway"]

    # ---- update ----
    def update(self, dt, bullets, player):
        if self.get_phase() != self.phase:
            self.start_phase(self.get_phase(), bullets)
        cfg = PHASES[self.phase]
        self.move(dt, cfg)
        if self.flash_timer > 0:
            self.flash_timer -= dt

        if self.transition_timer > 0:       # invulnerable and silent
            self.transition_timer -= dt
            return
        self.run_sequence(dt, cfg, bullets, player)

    # ---- draw ----
    def draw_background(self, surf):
        pass

    def draw(self, surf):
        self.sprite.draw(surf, self.x, self.y, flash=self.flashing())