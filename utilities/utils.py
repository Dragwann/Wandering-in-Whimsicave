import sys
import pygame

from utilities.settings import ASSET_DIR, WHITE

_image_cache = {}   # an image file is read from disk only once, however many times it is requested


def load_image(filename, size=None, height=None, alpha=True):
    """Load assets/<filename>. size=(w, h) stretches it, height=h keeps the ratio.
    Needs the pygame window to exist (convert / convert_alpha)."""
    key = (filename, size, height, alpha)
    if key in _image_cache:
        return _image_cache[key]

    path = ASSET_DIR / filename
    if not path.exists():
        sys.exit(f"Image introuvable : {path}\n"
                 f"Verifie que le dossier 'assets' est a la racine du projet et que le nom est exact.")
    img = pygame.image.load(path)
    img = img.convert_alpha() if alpha else img.convert()
    if size:
        img = pygame.transform.smoothscale(img, size)
    elif height:
        w = int(img.get_width() * height / img.get_height())
        img = pygame.transform.smoothscale(img, (w, height))

    _image_cache[key] = img
    return img


def white_silhouette(img):
    """Same shape as the sprite but entirely white (flash effect)."""
    return pygame.mask.from_surface(img).to_surface(setcolor=WHITE, unsetcolor=(0, 0, 0, 0))


def soften_background(img, dim, tint, blur):
    """Return a blurred + darkened COPY of the background (the cached original is left untouched)."""
    w, h = img.get_size()
    img = img.copy()
    if blur > 1:
        small = pygame.transform.smoothscale(img, (w // blur, h // blur))
        img = pygame.transform.smoothscale(small, (w, h))
    veil = pygame.Surface((w, h))
    veil.fill(tint)
    veil.set_alpha(int(255 * dim))
    img.blit(veil, (0, 0))
    return img