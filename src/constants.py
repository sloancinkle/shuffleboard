# --- Configuration & Constants ---
PPI = 7.0  # 7 pixels = 1 inch

# Dimensions
REAL_BOARD_WIDTH = 20   

# Visuals
LINE_WIDTH = 2 

# Zones
THROW_LINE_FT = 3     
FOUL_LINE_FT = 6      

# Puck Sizes (Inches)
PUCK_MEDIUM = 2.125   
PUCK_LARGE = 2.3125   

# Default Settings
DEFAULT_LENGTH_FT = 9 
DEFAULT_PUCK_SIZE = PUCK_MEDIUM

# Font Settings
PUCK_FONT_NAME = "couriernew" # Hardcoded per request

# Gutter Scaling (Relative to PPI)
GUTTER_LEFT_IN = 10.0
SCORE_GAP_IN = 4.0
GUTTER_RIGHT_IN = 5.0
GUTTER_Y_IN = 4

GUTTER_PADDING_LEFT = int(GUTTER_LEFT_IN * PPI)
GUTTER_PADDING_RIGHT = int(GUTTER_RIGHT_IN * PPI)
GUTTER_PADDING_Y = int(GUTTER_Y_IN * PPI)


# Icon sizes
ICON_SIZE_IN = 2.5 
ICON_SIZE_PX = int(ICON_SIZE_IN * PPI)

FPS = 60

# Colors
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)
DARK_GREY = (30, 30, 30)
GREY = (150, 150, 150)
BLUE = (60, 100, 220)
RED = (200, 50, 50)
WOOD_LIGHT = (222, 184, 135)
WOOD_DARK = (139, 69, 19)
TEXT_COLOR = (50, 50, 50)

# Player Logic Keys
P1 = "P1"
P2 = "P2"

# Visual Colors
PUCK_COLORS = {
    "Red": (240, 30, 20),
    "Wine": (120, 0, 30),
    "Orange": (220, 110, 0),
    "Yellow": (250, 220, 0),
    "Lime": (40, 210, 40),
    "Green": (0, 110, 20),
    "Cyan": (100, 200, 250),
    "Blue": (0, 70, 220),
    "Purple": (140, 30, 170),
    "Pink": (250, 100, 180),
    "White": (240, 240, 240)
}

# Physics
TABLE_FRICTION = 0.985 
GUTTER_FRICTION = 0.85 
MIN_SPEED = 0.05
MAX_POWER = 15.0

# Puck States
STATE_GUTTER = "GUTTER"         
STATE_READY = "READY"           
STATE_SELECTED = "SELECTED"     
STATE_THROWN = "THROWN"         
STATE_ON_BOARD = "ON_BOARD"