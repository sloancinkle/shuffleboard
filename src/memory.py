import json
import os
import sys
from .constants import P1, P2

def get_data_path():
    """
    Determines the correct, writable path for persistent data 
    depending on the Operating System.
    """
    app_name = "Shuffleboard"
    
    if sys.platform == "darwin":
        # macOS: ~/Library/Application Support/Shuffleboard/
        base_path = os.path.expanduser("~/Library/Application Support")
    elif sys.platform == "win32":
        # Windows: %LOCALAPPDATA%/Shuffleboard/
        base_path = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    else:
        # Linux: ~/.local/share/shuffleboard/
        base_path = os.path.expanduser("~/.local/share")

    full_path = os.path.join(base_path, app_name)
    
    if not os.path.exists(full_path):
        try:
            os.makedirs(full_path)
        except OSError:
            return os.path.expanduser("~")
            
    return full_path

MEMORY_FILE = os.path.join(get_data_path(), "memory.json")

def save_memory(game):
    # 1. Serialize Pucks
    puck_list = []
    for p in game.gutter.pucks:
        p_data = {
            "owner": p.owner,
            "x_in": p.x_in,
            "y_in": p.y_in,
            "state": p.state,
            "color": p.color
        }
        puck_list.append(p_data)

    # 2. Serialize Data
    data = {
        # --- Settings (Menu) ---
        "settings": {
            "length": game.board_length_ft,
            "puck_size": game.puck_size,
            "ppi": game.menu.ppi,
            "target_score": game.menu.target_score,
            "hangers": game.menu.hangers_enabled,
            
            # Visual Preferences
            "p1_color_name": game.menu.p1_color,
            "p2_color_name": game.menu.p2_color
            # REMOVED: Font and Text Color indices
        },

        # --- Gameplay Status ---
        "gameplay": {
            "current_turn": game.current_turn,
            "round_winner": game.round_winner,
            "throws_left_p1": game.throws_left[P1],
            "throws_left_p2": game.throws_left[P2],
            "game_over": game.game_over,
            "game_state": game.game_state,
            "state_timer_active": (game.game_state == "ROUND_OVER_DELAY")
        },

        # --- Scoreboard ---
        "scores": {
            "p1_score": game.scoreboard.p1_score,
            "p2_score": game.scoreboard.p2_score,
            "round_p1": game.scoreboard.round_points[P1],
            "round_p2": game.scoreboard.round_points[P2],
            "game_winner": game.scoreboard.game_winner
        },

        # --- Objects ---
        "pucks": puck_list
    }
    
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=4)
        return 0
    except Exception as e:
        return 1

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return None
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        return None