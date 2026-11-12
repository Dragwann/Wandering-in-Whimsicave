import math

from utilities.settings import ORANGE
from utilities.hitbox import Hitbox
from utilities.placeholder import PlaceholderSprite
from projectiles.hazards import String, STRING_TELEGRAPH_TIME

# Visuals (drop a PNG at HAND_*_IMAGE to replace the placeholder; the hitbox does not change)
HAND_LEFT_IMAGE = "entities/Hand_left_asset.png"
HAND_RIGHT_IMAGE = "entities/Hand_right_asset.png"
HAND_DRAW_HEIGHT = 110
HAND_PLACEHOLDER_SIZE = (80, 110)
HAND_COLOR = (230, 200, 170)
BACKGROUND_IMAGE = "backgrounds/Boss3_Miniboss3_background.png"   # cutter.py

# Cutter values
CUTTER_MAX_HP = 150                    # ONE pool for both hands
HAND_HITBOX_SIZE = (70, 100)           # rectangle hitbox of EACH hand (width, height)
HAND_REST_Y = 75
HAND_REST_X = (260, 700)               # left hand, right hand
HAND_STRING_OFFSET = 55                # the string starts this far below the hand center
HAND_ENTER_TIME = 1.0                  # hands come down from above, invulnerable
HAND_ENTER_OFFSET = 180
CUTTER_FIRST_ATTACK_DELAY = 0.7
HAND_MOVE_TIME = 0.5                   # hand slides to its attack position
HAND_RECOVER_TIME = 0.5                # hand slides back to its rest position
CUTTER_ATTACK_GAP = 0.3                # pause before the other hand starts
CUTTER_ENRAGED_TELEGRAPH = 0.65        # below 50% HP the warning is shorter

# (hand: 0 = left / 1 = right, x of the string). Predefined and alternating, loops forever.
CUTTER_SEQUENCE = [(0, 330), (1, 630), (0, 150), (1, 810), (0, 450), (1, 510)]


class Hand:
    """One hand: a position, a rectangle hitbox and a sprite. Health lives in Cutter (shared pool)."""

    def __init__(self, rest_x, image, label):
        self.rest_x = rest_x
        self.x, self.y = rest_x, HAND_REST_Y - HAND_ENTER_OFFSET
        self.hitboxes = [Hitbox.rect(self, *HAND_HITBOX_SIZE)]
        self.sprite = PlaceholderSprite(image, HAND_DRAW_HEIGHT, HAND_PLACEHOLDER_SIZE, HAND_COLOR, "rect", label)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class Cutter:
    """The Puppeteer's two hands. One hand at a time slides over a predefined x, shows a warning lane,
    shoots a String downward, then goes back; then the other hand plays.

    States: enter -> idle -> move -> attack (string alive) -> recover -> idle -> ...
    """

    max_hp = CUTTER_MAX_HP
    health_ticks = ()
    background_image = BACKGROUND_IMAGE      

    def __init__(self):
        self.hp = self.max_hp
        self.hands = [Hand(HAND_REST_X[0], HAND_LEFT_IMAGE, "HAND L"),
                      Hand(HAND_REST_X[1], HAND_RIGHT_IMAGE, "HAND R")]
        self.state = "enter"
        self.timer = HAND_ENTER_TIME
        self.attack_index = 0
        self.active = 0                    # hand currently attacking
        self.string = None                 # its string (only ONE at a time)
        self.move_from = 0.0
        self.move_to = 0.0

    # ---- interface shared by every boss / stage ----
    @property
    def hitboxes(self):
        return [box for hand in self.hands for box in hand.hitboxes]

    def invulnerable(self):
        return self.state == "enter"

    def deals_contact_damage(self):
        return not self.invulnerable()

    def take_hit(self, damage=1):
        if not self.invulnerable():
            self.hp -= damage

    def phase_color(self):
        return ORANGE

    def background_color(self):
        return (40, 22, 38)

    # ---- update ----
    def update(self, dt, bullets, player):
        hand = self.hands[self.active]

        if self.state == "enter":
            self.timer -= dt
            slide = smooth(self.timer / HAND_ENTER_TIME) * HAND_ENTER_OFFSET
            for h in self.hands:
                h.y = HAND_REST_Y - slide
            if self.timer <= 0:
                self.state, self.timer = "idle", CUTTER_FIRST_ATTACK_DELAY

        elif self.state == "idle":
            self.timer -= dt
            if self.timer <= 0:
                self.active, target_x = CUTTER_SEQUENCE[self.attack_index % len(CUTTER_SEQUENCE)]
                self.attack_index += 1
                hand = self.hands[self.active]
                self.move_from, self.move_to = hand.x, target_x
                self.state, self.timer = "move", HAND_MOVE_TIME

        elif self.state == "move":
            self.timer -= dt
            hand.x = self.move_from + (self.move_to - self.move_from) * smooth(1 - self.timer / HAND_MOVE_TIME)
            if self.timer <= 0:
                hand.x = self.move_to
                telegraph = CUTTER_ENRAGED_TELEGRAPH if self.hp <= self.max_hp / 2 else STRING_TELEGRAPH_TIME
                self.string = String(hand.x, hand.y + HAND_STRING_OFFSET, telegraph)
                bullets.append(self.string)
                self.state = "attack"

        elif self.state == "attack":
            # the string handles its own warning / extension / retraction; we only wait for it to end
            if self.string is None or self.string.dead:
                self.string = None
                self.move_from, self.move_to = hand.x, hand.rest_x
                self.state, self.timer = "recover", HAND_RECOVER_TIME

        elif self.state == "recover":
            self.timer -= dt
            hand.x = self.move_from + (self.move_to - self.move_from) * smooth(1 - self.timer / HAND_RECOVER_TIME)
            if self.timer <= 0:
                hand.x = hand.rest_x
                self.state, self.timer = "idle", CUTTER_ATTACK_GAP

    # ---- draw ----
    def draw_background(self, surf):
        pass

    def draw(self, surf):
        for i, hand in enumerate(self.hands):
            x, y = hand.x, hand.y
            warning = (i == self.active and self.string is not None and self.string.state == "telegraph")
            if warning:
                x += math.sin(self.string.timer * 60) * 3   # the hand trembles before shooting
            blink = self.state == "enter" and int(self.timer * 10) % 2 == 0
            hand.sprite.draw(surf, x, y, flash=blink or (warning and int(self.string.timer * 12) % 2 == 0))