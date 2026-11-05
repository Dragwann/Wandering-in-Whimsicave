import pygame

from utilities.settings import WIDTH, BLACK, WHITE


def draw_health_bar(surf, hp, max_hp, color):
    """Minimal health bar (no UI), with a tick at each phase change."""
    ratio = max(hp, 0) / max_hp
    bar_x = WIDTH // 2 - 150
    pygame.draw.rect(surf, BLACK, (bar_x - 2, 20, 304, 18))
    pygame.draw.rect(surf, color, (bar_x, 22, int(300 * ratio), 14))
    for tick in (1 / 3, 2 / 3):
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
