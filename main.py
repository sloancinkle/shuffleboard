import os
import sys

# 1. Clean up the console
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

# 2. Ensure we can import from the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 3. Import from the package 'src'
from src.game import Shuffleboard

if __name__ == "__main__":
    game = Shuffleboard()
    game.run()