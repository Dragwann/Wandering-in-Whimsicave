from collections import deque

from utilities.settings import WIDTH, HEIGHT, TEAL
from utilities.hitbox import Hitbox
from utilities.placeholder import PlaceholderSprite
from utilities.attack_patterns import fire_pattern, pat

# Visuals (drop a PNG at REFLECTION_IMAGE to replace the placeholder; the hitbox does not change)
REFLECTION_IMAGE = "entities/Reflection_asset.png"
REFLECTION_DRAW_HEIGHT = 100
REFLECTION_PLACEHOLDER_SIZE = (60, 100)
REFLECTION_COLOR = (150, 120, 255)
REFLECTION_ALPHA = 160                 # it is a ghost

# Reflection values
REFLECTION_MAX_HP = 150
REFLECTION_HITBOX_RADIUS = 32
REFLECTION_DELAY = 1.2                 # seconds behind the player (time based, never frames)
REFLECTION_SPAWN = (WIDTH - 130, HEIGHT // 2)
REFLECTION_ENTER_TIME = 1.0            # invulnerable and silent while it "materializes"
REFLECTION_FIRST_ATTACK_DELAY = 0.8
HISTORY_MAX_SAMPLES = 1024             # hard safety cap; the real bound is the time pruning below

FAN = {"type": "fan", "count": 1, "speed": 380, "radius": 13}
MINE_HERE = {"type": "mine", "at": "origin"}   # drops a mine where the reflection is = where YOU were

# (pattern, seconds before the next attack)
REFLECTION_SEQUENCE = [
    (pat(FAN, count=3, spread=30, speed=300), 1.2),
    (MINE_HERE, 1.0),
    (FAN, 0.6),
    (FAN, 1.0),
    ({"type": "ring", "count": 10, "speed": 230}, 1.6),
    (MINE_HERE, 1.0),
]


class PositionHistory:
    """Timestamped positions of the player: (time, x, y), oldest first.

    The time is the encounter's own clock (sum of dt), so reading "1.2 s ago" gives the same
    answer at 30, 60 or 144 FPS. Memory stays bounded: prune() drops what is older than needed.
    """

    def __init__(self):
        self.samples = deque(maxlen=HISTORY_MAX_SAMPLES)

    def __len__(self):
        return len(self.samples)

    def record(self, t, x, y):
        self.samples.append((t, x, y))

    def position_at(self, t):
        """Position at time t, interpolated between the two samples around it."""
        samples = self.samples
        if t <= samples[0][0]:
            return samples[0][1], samples[0][2]
        for i in range(1, len(samples)):
            t1, x1, y1 = samples[i]
            if t1 >= t:
                t0, x0, y0 = samples[i - 1]
                if t1 - t0 <= 1e-9:
                    return x1, y1
                a = (t - t0) / (t1 - t0)
                return x0 + (x1 - x0) * a, y0 + (y1 - y0) * a
        return samples[-1][1], samples[-1][2]

    def prune(self, oldest_needed):
        """Forget samples that can never be read again (keep the one just before `oldest_needed`)."""
        while len(self.samples) >= 2 and self.samples[1][0] <= oldest_needed:
            self.samples.popleft()


class Reflection:
    """Ghost that replays the player's POSITIONS `delay` seconds later (not the inputs).

    The history is seeded with the spawn point at t = -delay: at the start it glides from its spawn
    toward where the player began, then follows the recorded path. No jump, no missing history.
    """

    max_hp = REFLECTION_MAX_HP
    health_ticks = ()

    def __init__(self, delay=REFLECTION_DELAY):
        self.delay = delay
        self.x, self.y = REFLECTION_SPAWN
        self.hp = self.max_hp
        self.elapsed = 0.0                      # this stage's clock (sum of dt)
        self.history = PositionHistory()
        self.history.record(-delay, self.x, self.y)
        self.enter_timer = REFLECTION_ENTER_TIME
        self.step = 0
        self.attack_timer = REFLECTION_ENTER_TIME + REFLECTION_FIRST_ATTACK_DELAY
        self.hitboxes = [Hitbox.circle(self, REFLECTION_HITBOX_RADIUS)]
        self.sprite = PlaceholderSprite(REFLECTION_IMAGE, REFLECTION_DRAW_HEIGHT, REFLECTION_PLACEHOLDER_SIZE,
                                        REFLECTION_COLOR, "rect", "ECHO", REFLECTION_ALPHA)

    # ---- interface shared by every boss / stage ----
    def invulnerable(self):
        return self.enter_timer > 0

    def deals_contact_damage(self):
        return not self.invulnerable()

    def take_hit(self, damage=1):
        if not self.invulnerable():
            self.hp -= damage

    def phase_color(self):
        return TEAL

    def background_color(self):
        return (18, 28, 50)

    # ---- update ----
    def update(self, dt, bullets, player):
        self.elapsed += dt
        self.history.record(self.elapsed, player.x, player.y)
        target_time = self.elapsed - self.delay
        self.x, self.y = self.history.position_at(target_time)
        self.history.prune(target_time)

        if self.enter_timer > 0:
            self.enter_timer -= dt
            return

        self.attack_timer -= dt
        if self.attack_timer <= 0:
            spec, wait = REFLECTION_SEQUENCE[self.step % len(REFLECTION_SEQUENCE)]
            # Attacks start from the delayed position, so they come from "where you were".
            fire_pattern(spec, self.x, self.y, player, bullets)
            self.attack_timer = wait * (0.8 if self.hp <= self.max_hp / 2 else 1.0)
            self.step += 1

    # ---- draw ----
    def draw_background(self, surf):
        pass

    def draw(self, surf):
        blink = self.enter_timer > 0 and int(self.enter_timer * 10) % 2 == 0
        self.sprite.draw(surf, self.x, self.y, flash=blink)