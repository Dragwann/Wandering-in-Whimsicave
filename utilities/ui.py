import pygame

from utilities.settings import WIDTH, BLACK, WHITE

def draw_crosshair(surf, x, y, color=WHITE):
    """A ring with four ticks, centered on (x, y)."""
    x, y = int(x), int(y)
    pygame.draw.circle(surf, color, (x, y), 11, 2)
    pygame.draw.line(surf, color, (x - 20, y), (x - 7, y), 2)
    pygame.draw.line(surf, color, (x + 7, y), (x + 20, y), 2)
    pygame.draw.line(surf, color, (x, y - 20), (x, y - 7), 2)
    pygame.draw.line(surf, color, (x, y + 7), (x, y + 20), 2)
