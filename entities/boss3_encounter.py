import pygame

from utilities.settings import WIDTH, HEIGHT, WHITE
from utilities.placeholder import optional_image
from utilities.utils import soften_background
from entities.minibosses.twins import Twins
from entities.minibosses.reflection import Reflection
from entities.minibosses.cutter import Cutter
from entities.puppeteer import Puppeteer

# (name, subtitle, class). The encounter plays them in this order, one at a time.
STAGES = [
    ("The Twins", "Two puppets, one heart", Twins),
    ("The Reflection", "It remembers where you were", Reflection),
    ("The Cutter", "Mind the strings", Cutter),
    ("The Puppeteer", "The strings were always his", Puppeteer),
]

ENCOUNTER_INTRO_TIME = 2.2      # banner before the first stage
STAGE_TRANSITION_TIME = 1.8     # short pause between two stages (the player can still move and shoot)

# Background: if the image exists it is used (dimmed, with the stage color as a veil); otherwise the
# stage color fills the screen. Drop the file at this path to replace the placeholder.
BACKGROUND_IMAGE = "backgrounds/Boss3_background.jpg"
BACKGROUND_DIM = 0.35
BACKGROUND_TINT = (15, 10, 30)
BACKGROUND_BLUR = 3
BACKGROUND_VEIL_ALPHA = 110


class Boss3Encounter:
    """Four fights in a row (Twins -> Reflection -> Cutter -> Puppeteer) behind the SAME interface as
    Boss / Boss2, so main.py treats it like any other boss.

    Only one stage is alive at a time (`self.stage`). The encounter only does the bookkeeping:
    progression, transitions, and forwarding of update / draw / hitboxes / take_hit.

    hp / max_hp are those of the CURRENT stage, and hp only reaches 0 when the Puppeteer dies:
    that is what keeps main.py's "boss.hp <= 0 -> win" rule correct.

    state: "transition" (banner, nothing to hit) -> "fight" -> "transition" -> ... -> "victory"
    """

    def __init__(self):
        self.stage_index = 0
        self.stage = STAGES[0][2]()
        self.state = "transition"
        self.timer = ENCOUNTER_INTRO_TIME
        self.timer_total = ENCOUNTER_INTRO_TIME
        self.bullets = None                 # the boss_bullets list (given by update, used for cleanup)
        self.title_font = pygame.font.SysFont("arial", 56)
        self.sub_font = pygame.font.SysFont("arial", 26)
        self.label_font = pygame.font.SysFont("arial", 22)

        self.background = optional_image(BACKGROUND_IMAGE, size=(WIDTH, HEIGHT), alpha=False)
        if self.background is not None:
            self.background = soften_background(self.background, BACKGROUND_DIM, BACKGROUND_TINT, BACKGROUND_BLUR)
        self.veil = pygame.Surface((WIDTH, HEIGHT))
        self.veil.set_alpha(BACKGROUND_VEIL_ALPHA)

    # ---- the interface main.py and the CollisionManager use ----
    @property
    def hitboxes(self):
        """Hitboxes of the active stage (both puppets / both hands included); nothing between stages."""
        return self.stage.hitboxes if self.state == "fight" else []

    @property
    def hp(self):
        return self.stage.hp

    @hp.setter
    def hp(self, value):
        if self.state == "fight":           # debug keys 1/2/3 write boss.hp
            self.stage.hp = value

    @property
    def max_hp(self):
        return self.stage.max_hp

    @property
    def health_ticks(self):
        return self.stage.health_ticks

    @property
    def x(self):
        return getattr(self.stage, "x", WIDTH // 2)

    @property
    def y(self):
        return getattr(self.stage, "y", HEIGHT // 2)

    def invulnerable(self):
        return self.state != "fight" or self.stage.invulnerable()

    def deals_contact_damage(self):
        return self.state == "fight" and self.stage.deals_contact_damage()

    def phase_color(self):
        return self.stage.phase_color()

    def take_hit(self, damage=1):
        if self.state != "fight":
            return                          # several bullets can land in the frame a stage dies
        self.stage.take_hit(damage)
        if self.stage.hp <= 0:
            self.stage_defeated()

    # ---- progression ----
    def stage_defeated(self):
        # Boss hazards only ever belong to the active boss (same rule as Boss 1 / Boss 2 phase changes),
        # so clearing the list removes this stage's bullets, strings, mines and walls, and nothing else.
        if self.bullets is not None:
            self.bullets.clear()
        if self.stage_index == len(STAGES) - 1:
            self.state = "victory"          # the Puppeteer stays as the current stage, with hp <= 0
            return
        self.stage_index += 1
        self.stage = STAGES[self.stage_index][2]()
        self.state = "transition"
        self.timer = self.timer_total = STAGE_TRANSITION_TIME

    def debug_skip(self):
        """Debug (K key): kill the current stage."""
        if self.state == "fight":
            self.stage.hp = 0
            self.stage_defeated()

    # ---- update ----
    def update(self, dt, bullets, player):
        self.bullets = bullets
        if self.state == "transition":
            self.timer -= dt
            if self.timer <= 0:
                self.state = "fight"
        elif self.state == "fight":
            self.stage.update(dt, bullets, player)

    # ---- draw ----
    def draw_background(self, surf):
        color = self.stage.background_color()
        if self.background is not None:
            surf.blit(self.background, (0, 0))
            self.veil.fill(color)
            surf.blit(self.veil, (0, 0))
        else:
            surf.fill(color)

    def draw(self, surf):
        if self.state == "fight":
            self.stage.draw(surf)
        elif self.state == "transition":
            self.draw_banner(surf)
        name = STAGES[self.stage_index][0]
        label = self.label_font.render(f"{self.stage_index + 1}/{len(STAGES)}  {name}", True, WHITE)
        surf.blit(label, (10, 44))

    def draw_banner(self, surf):
        """Stage name in the middle of the screen, fading in and out."""
        name, subtitle, _ = STAGES[self.stage_index]
        elapsed = self.timer_total - self.timer
        alpha = int(255 * max(0.0, min(1.0, elapsed / 0.3, self.timer / 0.4)))
        for text, font, y in ((name, self.title_font, HEIGHT // 2 - 20), (subtitle, self.sub_font, HEIGHT // 2 + 30)):
            img = font.render(text, True, WHITE)
            img.set_alpha(alpha)
            surf.blit(img, img.get_rect(center=(WIDTH // 2, y)))