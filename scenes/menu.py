"""Boss select screen.

Layout (see the mockup): a big parchment at the top holding the boss icons (name under each),
the narrator standing at the bottom right, and an EXIT button at the bottom.
The arrows on the sides of the parchment flip between pages of icons (normal / intermediate / hardcore).

Every picture is optional: drop the PNG at the path below and the placeholder is replaced
automatically (same system as utilities/placeholder.py).
"""
import pygame

from utilities.settings import WIDTH, HEIGHT, BACKGROUND_COLOR, WHITE, ORANGE, JOY_BTN_SHOOT, ASSET_DIR
from utilities.placeholder import PlaceholderSprite, optional_image
from utilities.utils import soften_background

BOSS_NAMES = ["James Pines", "Dr. Maurice", "The Puppeteer"]
BOSS_ICONS = ["ui/Boss1_icon.png", "ui/Boss2_icon.png", "ui/Boss3_icon.png"]   # optional, CARD_SIZE px
MENU_BACKGROUND = "backgrounds/Menu_background.jpg"                              # optional
NARRATOR_IMAGE = "entities/Narrator_Frog_2.png"   # "entities/Narrator_Frog.png" once the art is ready (None = grey placeholder)
PARCHMENT_IMAGE = None  # "ui/parchment.png" once the art is ready (None = grey placeholder)
FONT_FILE = ASSET_DIR / "ui/font/pixeloid/PixeloidSans-Bold.ttf"
NARRATOR_NAME = "fauvelet linnielincy wineruthswith"

# Pages of icons, as indexes into BOSS_NAMES / BOSS_ICONS. For now only the normal page exists:
# add [3, 4, 5] etc. here when the intermediate / hardcore icons are ready (the arrows turn on by themselves).
PAGES = [[0, 1, 2]]

EXIT_LABEL = "EXIT"

# Background: same veil as the boss backgrounds (see BACKGROUND_* in boss1.py / boss2.py)
BACKGROUND_DIM = 0.45          # 0 = background untouched, 1 = fully black
BACKGROUND_TINT = (15, 10, 30) # color of the veil laid over the background
BACKGROUND_BLUR = 2            # 1 = no blur, 2-4 = softer details

# ---- layout (screen pixels, 960x540) ----
BUBBLE = pygame.Rect(60, 20, 760, 290)          # the parchment (stretched to this size)
CARD_SIZE = (150, 170)
CARD_GAP = 40
CARD_TOP = BUBBLE.top + 22
NAME_Y = CARD_TOP + CARD_SIZE[1] + 40           # center of the boss name, under the icon
ARROW_INSET = 50                                # arrow center, distance from the bubble sides
ARROW_SIZE = (28, 50)
NARRATOR_CENTER = (820, 380)                    # bottom-right corner: right edge at the screen edge, bottom 20 px above it
NARRATOR_HEIGHT = 280
NARRATOR_TAG_GAP = 6                            # px between the name tag and the top of the narrator
EXIT_RECT = pygame.Rect(140, 470, 440, 46)

# ---- colors ----
CARD_COLOR = (153, 0, 0)                    # grey placeholder for missing icons
BUBBLE_PLACEHOLDER_COLOR = (0, 0, 0)            # shown instead of the parchment while PARCHMENT_IMAGE is None
ARROW_COLOR = (120, 85, 50)                     # brown, readable on the parchment
ARROW_OFF_COLOR = (190, 165, 130)
FOCUS_COLOR = (190, 165, 130)

# ---- pixel-art text ----
FONT_SIZE = 9                                   # Pixeloid's native size: keep it (or a multiple of 9) to stay crisp
PIXEL_SCALE = 2                                 # menu text is drawn at native size, then enlarged x2
TAG_SCALE = 1.2                                   # narrator name tag (long name: x1 keeps it short)
PLAQUE_BG = (38, 28, 48)
PLAQUE_BORDER = (200, 170, 110)
PLAQUE_SHADOW = (18, 12, 26)
TAG_BG = (0, 0, 0, 130)                         # Minecraft-style name tag: translucent black


def load_pixel_font(size=FONT_SIZE):
    """The Pixeloid font from assets/ui/font, or a system font if the file is missing."""
    if FONT_FILE.exists():
        return pygame.font.Font(str(FONT_FILE), size)
    return pygame.font.SysFont("arial", size + 3, bold=True)


def pixel_text(font, text, color, scale=PIXEL_SCALE):
    """Hard-edged, blocky text: render without anti-aliasing, then enlarge without smoothing."""
    img = font.render(text, False, color)
    if scale == 1:
        return img
    return pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))


def draw_pixel_plaque(surf, rect, border=PLAQUE_BORDER, bg=PLAQUE_BG, step=4):
    """A rectangle with stepped ("notched") corners and a 1-step border: the pixel-art look."""
    x, y, w, h = rect
    # drop shadow
    pygame.draw.rect(surf, PLAQUE_SHADOW, (x + step, y + step, w, h))
    # border = full rect minus the corner pixels, then the fill one step inside
    pygame.draw.rect(surf, border, (x + step, y, w - 2 * step, h))
    pygame.draw.rect(surf, border, (x, y + step, w, h - 2 * step))
    pygame.draw.rect(surf, bg, (x + step, y + step, w - 2 * step, h - 2 * step))
    pygame.draw.rect(surf, bg, (x + 2 * step, y + step, w - 4 * step, h - 2 * step))


def draw_label(surf, text_img, center, pad_x=14, pad_y=8, **kw):
    """Pixel plaque sized around an already-rendered text image, centered on `center`."""
    rect = pygame.Rect(0, 0, text_img.get_width() + 2 * pad_x, text_img.get_height() + 2 * pad_y)
    rect.center = center
    draw_pixel_plaque(surf, rect, **kw)
    surf.blit(text_img, text_img.get_rect(center=rect.center))
    return rect


class Menu:
    def __init__(self):
        self.page = 0
        self.selected = 0          # card index inside the current page
        self.on_exit = False       # keyboard / mouse focus is on the EXIT button
        self.font = load_pixel_font()

        background = optional_image(MENU_BACKGROUND, size=(WIDTH, HEIGHT), alpha=False)
        self.background = (soften_background(background, BACKGROUND_DIM, BACKGROUND_TINT, BACKGROUND_BLUR)
                           if background else None)
        self.parchment = optional_image(PARCHMENT_IMAGE, size=BUBBLE.size)
        self.narrator = PlaceholderSprite(NARRATOR_IMAGE, height=NARRATOR_HEIGHT,
                                          size=(int(NARRATOR_HEIGHT * 0.46), NARRATOR_HEIGHT),
                                          color=(217, 217, 217), label="NARRATEUR")
        self.icons = [optional_image(path, size=CARD_SIZE) for path in BOSS_ICONS]

        arrow_y = CARD_TOP + CARD_SIZE[1] // 2
        self.left_arrow = pygame.Rect(0, 0, *ARROW_SIZE)
        self.left_arrow.center = (BUBBLE.left + ARROW_INSET, arrow_y)
        self.right_arrow = pygame.Rect(0, 0, *ARROW_SIZE)
        self.right_arrow.center = (BUBBLE.right - ARROW_INSET, arrow_y)

    # ---------- layout helpers ----------
    @property
    def boss_indexes(self):
        return PAGES[self.page]

    @property
    def has_pages(self):
        return len(PAGES) > 1

    def card_rects(self):
        n = len(self.boss_indexes)
        total = n * CARD_SIZE[0] + (n - 1) * CARD_GAP
        x = BUBBLE.centerx - total // 2
        return [pygame.Rect(x + i * (CARD_SIZE[0] + CARD_GAP), CARD_TOP, *CARD_SIZE) for i in range(n)]

    # ---------- input ----------
    def handle_event(self, event):
        """Returns ("start", boss_index), ("quit", None) or None."""
        if event.type == pygame.MOUSEMOTION:
            self._hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._hover(event.pos)
            return self._click(event.pos)
        elif event.type == pygame.KEYDOWN:
            return self._key(event.key)
        elif event.type == pygame.JOYHATMOTION:
            hat_keys = {(-1, 0): pygame.K_LEFT, (1, 0): pygame.K_RIGHT, (0, 1): pygame.K_UP, (0, -1): pygame.K_DOWN}
            if tuple(event.value) in hat_keys:
                return self._key(hat_keys[tuple(event.value)])
        elif event.type == pygame.JOYBUTTONDOWN and event.button == JOY_BTN_SHOOT:
            return self._validate()
        return None

    def _hover(self, pos):
        for i, rect in enumerate(self.card_rects()):
            if rect.collidepoint(pos):
                self.selected, self.on_exit = i, False
                return
        if EXIT_RECT.collidepoint(pos):
            self.on_exit = True

    def _click(self, pos):
        if self.left_arrow.inflate(30, 30).collidepoint(pos):
            self._turn_page(-1)
        elif self.right_arrow.inflate(30, 30).collidepoint(pos):
            self._turn_page(1)
        elif EXIT_RECT.collidepoint(pos):
            return ("quit", None)
        elif any(rect.collidepoint(pos) for rect in self.card_rects()):
            return self._validate()
        return None

    def _key(self, key):
        last = len(self.boss_indexes) - 1
        if key == pygame.K_LEFT and not self.on_exit:
            if self.selected > 0:
                self.selected -= 1
            else:
                self._turn_page(-1)
        elif key == pygame.K_RIGHT and not self.on_exit:
            if self.selected < last:
                self.selected += 1
            else:
                self._turn_page(1)
        elif key == pygame.K_UP:
            self.on_exit = False
        elif key == pygame.K_DOWN:
            self.on_exit = True
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            return self._validate()
        elif key == pygame.K_ESCAPE:
            return ("quit", None)
        return None

    def _turn_page(self, step):
        if not self.has_pages:
            return
        self.page = (self.page + step) % len(PAGES)
        self.selected = 0 if step > 0 else len(self.boss_indexes) - 1

    def _validate(self):
        if self.on_exit:
            return ("quit", None)
        return ("start", self.boss_indexes[self.selected])

    # ---------- drawing ----------
    def draw(self, surf):
        if self.background:
            surf.blit(self.background, (0, 0))
        else:
            surf.fill(BACKGROUND_COLOR)

        # the parchment (grey rectangle while parchment.png is missing)
        if self.parchment:
            surf.blit(self.parchment, BUBBLE)
        else:
            pygame.draw.rect(surf, BUBBLE_PLACEHOLDER_COLOR, BUBBLE)

        # narrator + his name tag, Minecraft style (translucent black box, white text, above the head)
        # the last word of the name goes on a second line
        self.narrator.draw(surf, *NARRATOR_CENTER)
        lines = [pixel_text(self.font, line, WHITE, TAG_SCALE) for line in NARRATOR_NAME.rsplit(" ", 1)]
        line_gap = 2
        text_w = max(img.get_width() for img in lines)
        text_h = sum(img.get_height() for img in lines) + line_gap * (len(lines) - 1)
        tag = pygame.Surface((text_w + 12, text_h + 8), pygame.SRCALPHA)
        tag.fill(TAG_BG)
        y = 4
        for img in lines:
            tag.blit(img, img.get_rect(midtop=(tag.get_width() // 2, y)))
            y += img.get_height() + line_gap
        tag_rect = tag.get_rect(midbottom=(NARRATOR_CENTER[0],
                                           NARRATOR_CENTER[1] - NARRATOR_HEIGHT // 2 - NARRATOR_TAG_GAP))
        tag_rect.right = min(tag_rect.right, WIDTH - 6)     # never leave the screen
        surf.blit(tag, tag_rect)

        # boss cards + names
        for i, (rect, boss) in enumerate(zip(self.card_rects(), self.boss_indexes)):
            icon = self.icons[boss] if boss < len(self.icons) else None
            if icon:
                surf.blit(icon, rect)
            else:
                pygame.draw.rect(surf, CARD_COLOR, rect, border_radius=14)
            if i == self.selected and not self.on_exit:
                pygame.draw.rect(surf, FOCUS_COLOR, rect.inflate(10, 10), 4, border_radius=18)
            name = pixel_text(self.font, BOSS_NAMES[boss], WHITE)
            draw_label(surf, name, (rect.centerx, NAME_Y), pad_x=10)

        # page arrows (dimmed while there is only one page)
        arrow_color = ARROW_COLOR if self.has_pages else ARROW_OFF_COLOR
        r = self.left_arrow
        pygame.draw.polygon(surf, arrow_color, [(r.right, r.top), (r.right, r.bottom), (r.left, r.centery)])
        r = self.right_arrow
        pygame.draw.polygon(surf, arrow_color, [(r.left, r.top), (r.left, r.bottom), (r.right, r.centery)])

        # exit button: a pixel plaque the size of EXIT_RECT
        draw_pixel_plaque(surf, EXIT_RECT, border=FOCUS_COLOR if self.on_exit else PLAQUE_BORDER)
        label = pixel_text(self.font, EXIT_LABEL, WHITE)
        surf.blit(label, label.get_rect(center=EXIT_RECT.center))
