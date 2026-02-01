# Shuffleboard

A realistic, physics-based 2-player table shuffleboard game built for macOS.

![Game Screenshot](screenshots/gameplay.png)

## Download
**Currently available for macOS only.**

[**Download Shuffleboard for Mac (Google Drive)**](https://drive.google.com/file/d/1vKc4h0UFCQ1bH6R-a3DQM6Tk1YMgJxbc/view?usp=drive_link#)

---

## Installation Instructions
Because this application is not signed by Apple, you will need to bypass the security check once upon first launch.

1. Download the .zip file from the link above and unzip it.
2. Right-click (or Control-click) the Shuffleboard app icon and select Open.
3. A warning dialog will appear. Click Open (or "Open Anyway").
4. If prompted, open your Mac's System Settings > Privacy & Security, scroll to the bottom, and click Open Anyway next to the Shuffleboard notification.
5. Enter your user password if prompted.

Note: You only need to do this the first time. Afterwards, you can double-click the app to run it.

---

## How to Play

### Controls
1. Grab: Hover your mouse over one of your pucks in the gutter area, and click and hold to grab the puck.
2. Throw: Drag the mouse forward quickly and release the mouse while inside the throw area. 

### Objective
The goal is to slide your pucks to the opposite end of the table into the scoring zones without falling off the end or sides. You can also try to knock your opponent's pucks off the board.

### Scoring
Points are awarded based on where the puck stops:
* 1 Point: Closest zone.
* 2 Points: Middle zone.
* 3 Points: Furthest zone.
* 4 Points (Optional): A puck hanging partially off the back edge of the board.

Only the player with the furthest puck scores points for the round. They receive points for every puck that is ahead of their opponent's furthest puck.

---

## The Scoreboard
The digital scoreboard tracks the game state in real-time.

![Scoreboard Screenshot](screenshots/scoreboard.png)

* Main Score: The total accumulated score for the game.
* Turn Indicator: Indicates whose turn it is to throw.
* Round Score: Shows how many points would be added to your main score if the round ended. This updates instantly as pucks move.
* Throws Remaining: The dashes at the bottom represent your pucks. Each player gets 4 throws per round.

---

## Game Options & Settings
Click the Menu Icon (top right) to open the Options Screen.

![Options Screenshot](screenshots/options.png)
*(Place a screenshot of the options menu here)*

### Table Settings
* Window Size (Arrows): Increases or decreases the PPI (Pixels Per Inch), effectively zooming the game window in or out to fit your screen.
* Table Length (Slider): Adjusts the physical length of the board from 9 feet to 22 feet.
* Puck Size: Cycles between Large (2 5/16 inches) and Medium (2 1/8 inches).
    * Note: The game automatically defaults to Medium for tables under 15ft and Large for tables 15ft+, but you can override this manually.
* Game Goal: Toggle between playing a game to 15 or 21 points.
* Hangers Rule: Toggle scoring for "Hangers" (pucks hanging off the edge) between 4 points and 3 points.

### Player Customization
* Color Selection: The two wooden tables on the right allow you to choose puck colors.
    * Top Table: Player 1 (Scoreboard Left).
    * Bottom Table: Player 2 (Scoreboard Right).
    * Tip: You can practice throwing pucks on these mini-tables to test the friction!

### Resume vs. Reset
* RESUME: Returns you to the current game without changes.
* RESET: If you change a setting that affects gameplay (Table Length, Puck Size, Rules), the button will change to RESET. Clicking this will apply changes and start a new match.

---

## Saving & Memory
The game automatically saves your progress (score, puck positions, current turn) and your settings preferences.

When does it save?
* When you click the 'X' button to close the window.
* When you press 'Start/Resume' in the menu.

Important Warning:
If you force quit the app using Command+Q, the game will not save the current state. Close the window using the red 'X' button to ensure your game is saved.

### Managing Save Data
The save file is located securely in your Mac's Application Support folder:
~/Library/Application Support/Shuffleboard/memory.json

To reset everything to default (delete your save):
1. Open Finder.
2. Press Cmd + Shift + G.
3. Paste: ~/Library/Application Support/Shuffleboard/
4. Delete memory.json.