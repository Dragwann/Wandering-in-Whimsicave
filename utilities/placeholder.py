"""Placeholder art for entities that have no asset yet.

PlaceholderSprite draws the real image if the file exists in assets/, otherwise a labelled,
colored shape. When the art arrives, drop the PNG at the path stored in the entity's *_IMAGE
constant and the placeholder is replaced automatically: nothing else to change.

The sprite size is NOT the hitbox size. Every entity keeps its hitbox in its own constant
(Hitbox.circle / Hitbox.rect), so new art never changes how the collisions feel.
"""
import pygame

from utilities.settings import ASSET_DIR, WHITE
from utilities.utils import load_image, white_silhouette

_font = None


def _label_font():
    global _font
    if _font is None:
        _font = pygame.font.SysFont("arial", 16, bold=True)
    return _font


def optional_image(filename, size=None, height=None, alpha=True):
    """Like load_image, but returns None (instead of quitting the game) if the file does not exist."""
    if not filename or not (ASSET_DIR / filename).exists():
        return None
    return load_image(filename, size=size, height=height, alpha=alpha)


def _placeholder_surface(size, color, shape, label, alpha):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    rect = surf.get_rect()
    dark = tuple(int(c * 0.45) for c in color)
    if shape == "ellipse":
        pygame.draw.ellipse(surf, color, rect)
        pygame.draw.ellipse(surf, dark, rect, 3)
    else:
        pygame.draw.rect(surf, color, rect, border_radius=10)
        pygame.draw.rect(surf, dark, rect, 3, border_radius=10)
    if label:
        text = _label_font().render(label, True, dark)
        surf.blit(text, text.get_rect(center=rect.center))
    if alpha < 255:
        surf.set_alpha(alpha)
    return surf


class PlaceholderSprite:
    """filename: asset path (relative to assets/), or None. height: on-screen height of the real image.
    size / color / shape ("rect" or "ellipse") / label: what is drawn while there is no image."""

    def __init__(self, filename, height, size, color, shape="rect", label="", alpha=255):
        image = optional_image(filename, height=height)
        self.has_asset = image is not None
        if self.has_asset:
            self.normal = image.copy() if alpha < 255 else image   # never alter the shared cached image
            self.flash = white_silhouette(image)
            if alpha < 255:
                self.normal.set_alpha(alpha)
                self.flash.set_alpha(alpha)
        else:
            self.normal = _placeholder_surface(size, color, shape, label, alpha)
            self.flash = _placeholder_surface(size, WHITE, shape, label, alpha)

    def draw(self, surf, x, y, flash=False):
        img = self.flash if flash else self.normal
        surf.blit(img, img.get_rect(center=(int(x), int(y))))