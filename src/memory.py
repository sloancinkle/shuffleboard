import json
import os
import sys
from . import constants

def get_data_path():
    """
    Returns the path to the user's Application Support folder for data storage.
    """
    if sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    elif sys.platform == "win32":
        base = os.getenv("APPDATA")
    else:
        base = os.path.expanduser("~/.local/share")
    
    path = os.path.join(base, "Shuffleboard")
    if not os.path.exists(path):
        os.makedirs(path)
    return os.path.join(path, "memory.json")

def save_memory(game):
    data = {
        "settings": {
            "length": game.board_length_ft,
            "puck_size": game.puck_size,
            "ppi": constants.PPI,
            "target_score": game.menu.target_score,
            "edging": game.menu.edging_enabled,
            "p1_color_name": game.menu.p1_color,
            "p2_color_name": game.menu.p2_color
        },
        "scores": {
            "p1_score": game.scoreboard.p1_score,
            "p2_score": game.scoreboard.p2_score,
            "round_p1": game.scoreboard.round_points[constants.P1],
            "round_p2": game.scoreboard.round_points[constants.P2],
            "game_winner": game.scoreboard.game_winner
        },
        "gameplay": {
            "current_turn": game.current_turn,
            "round_winner": game.round_winner,
            "throws_left_p1": game.throws_left[constants.P1],
            "throws_left_p2": game.throws_left[constants.P2],
            "game_over": game.game_over,
            "game_state": game.game_state,
            "state_timer_active": (game.state_timer != 0)
        },
        "pucks": []
    }

    for p in game.gutter.pucks:
        p_data = {
            "owner": p.owner,
            "x_in": p.x_in,
            "y_in": p.y_in,
            "dx": p.dx,
            "dy": p.dy,
            "is_moving": p.is_moving,
            "state": p.state,
            "color": p.color
        }
        data["pucks"].append(p_data)

    try:
        with open(get_data_path(), 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Failed to save game data: {e}")

def load_memory():
    path = get_data_path()
    if not os.path.exists(path):
        return None
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load game data: {e}")
        return None