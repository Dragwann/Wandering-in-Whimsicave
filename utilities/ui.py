import pygame

from utilities.settings import WIDTH, BLACK, WHITE, HEIGHT
from utilities.utils import load_image

LIFE_MARGIN = 15               # distance from the screen edges (px)
LIFE_COUNTER_HEIGHT = 35       # height of the rectangle (px), width keeps the image ratio
LIFE_ICON_HEIGHT = 25          # height of each life icon (px)
LIFE_ICON_GAP = 7             # space between the rectangle and the first icon
LIFE_ICON_SPACING = 5          # space between two icons
LIFE_ICON_BLINK_TIME = 1.0 


def draw_health_bar(surf, hp, max_hp, color, ticks=(1 / 3, 2 / 3)):
    """Minimal health bar (no UI), with a tick at each phase change (ticks = HP fractions, () for none)."""
    ratio = max(hp, 0) / max_hp
    bar_x = WIDTH // 2 - 150
    pygame.draw.rect(surf, BLACK, (bar_x - 2, 20, 304, 18))
    pygame.draw.rect(surf, color, (bar_x, 22, int(300 * ratio), 14))
    for tick in ticks:
        tx = bar_x + int(300 * tick)
        pygame.draw.line(surf, WHITE, (tx, 20), (tx, 38), 2)


def draw_crosshair(surf, x, y, color=WHITE):
    """A ring with four ticks, centered on (x, y)."""
    x, y = int(x), int(y)
    pygame.draw.circle(surf, color, (x, y), 11, 2)
    pygame.draw.line(surf, color, (x - 20, y), (x - 7, y), 2)
    pygame.draw.line(surf, color, (x + 7, y), (x + 20, y), 2)
    pygame.draw.line(surf, color, (x, y - 20), (x, y - 7), 2)
    pygame.draw.line(surf, color, (x, y + 7), (x, y + 20), 2)

class LifeCounter:
    def __init__(self, max_lives=3):
        self.max_lives = max_lives
        self.prev_lives = max_lives
        self.blink = {}        # slot index -> remaining blink time, for icons that were just lost
        self.counters = {n: load_image(f"ui/player_life_counter_{n}.png", height=LIFE_COUNTER_HEIGHT)
                         for n in range(1, max_lives + 1)}
        self.icon = load_image("ui/player_life.png", height=LIFE_ICON_HEIGHT)
        # icons start after the widest rectangle, so they never jump when the number changes
        self.counter_width = max(img.get_width() for img in self.counters.values())
 
    def update(self, dt, lives):
        if lives < self.prev_lives:
            for slot in range(lives, self.prev_lives):
                self.blink[slot] = LIFE_ICON_BLINK_TIME
        self.prev_lives = lives
        for slot in list(self.blink):
            self.blink[slot] -= dt
            if self.blink[slot] <= 0:
                del self.blink[slot]
 
    def draw(self, surf, lives):
        counter = self.counters[max(1, min(lives, self.max_lives))]
        y = HEIGHT - LIFE_MARGIN - counter.get_height()
        surf.blit(counter, (LIFE_MARGIN, y))
 
        icon_y = y + (counter.get_height() - self.icon.get_height()) // 2
        x = LIFE_MARGIN + self.counter_width + LIFE_ICON_GAP
        for slot in range(self.max_lives):          # a lost life leaves an empty slot, icons never shift
            show = slot < lives
            if not show and slot in self.blink:
                show = int(self.blink[slot] * 10) % 2 == 0   # blinking, then gone
            if show:
                surf.blit(self.icon, (x, icon_y))
            x += self.icon.get_width() + LIFE_ICON_SPACING