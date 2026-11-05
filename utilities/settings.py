# Global settings: screen, colors, and values shared by several files.
# Values that belong to ONE behavior live next to that behavior
# (projectiles.py, hazards.py, boss1.py, boss2.py).

# Config
WIDTH, HEIGHT = 960, 540
FPS = 60
DEBUG_KEYS = True  # 1/2/3 = jump to boss phase 1/2/3, G = toggle god mode
TITLE = "Wandering in Whimsicave"
BACKGROUND_COLOR = (25, 20, 35)

# Player Values
PLAYER_RADIUS = 14
PLAYER_SPEED = 320            # px/s
PLAYER_SHOOT_COOLDOWN = 0.1
PLAYER_BULLET_SPEED = 520
PLAYER_BULLET_RADIUS = 5

# Controller (button numbers differ between pads, adjust if yours is off)
JOY_DEADZONE = 0.2             # ignore stick values smaller than this
JOY_BTN_SHOOT = 0              # A on Xbox / Cross on PlayStation
JOY_BTN_RESTART = 7            # Start on Xbox
JOY_AXIS_AIM_X = 2             # right stick, horizontal (axis numbers differ between pads!)
JOY_AXIS_AIM_Y = 3             # right stick, vertical
JOY_AIM_DEADZONE = 0.3         # right stick below this = "not aiming"
JOY_STICK_AUTOFIRE = True      # pushing the right stick fires (your thumb is busy on the stick)
CROSSHAIR_DISTANCE = 110       # px between player and crosshair when aiming with the stick

# Colors Values
WHITE = (240, 240, 240)
BLACK = (10, 10, 10)
RED = (220, 60, 60)
ORANGE = (240, 150, 50)
CRIMSON = (150, 20, 60)
BLUE = (90, 160, 255)
PURPLE = (170, 90, 220)
GREEN = (90, 220, 120)
YELLOW = (240, 210, 90)
PINK = (240, 120, 200)
TEAL = (60, 200, 190)
WARNING = (255, 120, 120)
