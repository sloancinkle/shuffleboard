import pygame
import random
import time
from .. import constants 
from ..constants import STATE_ON_BOARD, STATE_THROWN, STATE_SELECTED, BLACK, DARK_GREY, WHITE, P1, P2, PUCK_COLORS

class Scoreboard:
    def __init__(self):
        self.round_font = pygame.font.SysFont("arial", 24, bold=True)
        self.p1_score = 0
        self.p2_score = 0
        self.round_points = {P1: 0, P2: 0}
        self.game_winner = None 
        
        self.flash_timers = {} 
        self.flash_colors = {}

    def reset(self):
        self.p1_score = 0
        self.p2_score = 0
        self.round_points = {P1: 0, P2: 0}
        self.game_winner = None
        self.flash_timers = {}
        self.flash_colors = {}

    def calculate_points(self, active_pucks, board_length_ft, edging_enabled, game_over):
        valid = []
        for p in active_pucks:
            if p.state in (STATE_ON_BOARD, STATE_THROWN):
                valid.append(p)
            elif p.state == STATE_SELECTED:
                if game_over:
                    valid.append(p)
        
        points = {P1: 0, P2: 0}
        
        if not valid: 
            self.round_points = points
            return
        
        # Sort by distance (x_in) descending
        valid.sort(key=lambda p: p.x_in, reverse=True)
        
        # Check if the lead is tied between different owners
        leader = valid[0]
        if len(valid) > 1 and valid[1].x_in == leader.x_in and valid[1].owner != leader.owner:
            self.round_points = points # Tie at the top, no one scores
            return

        leader_owner = leader.owner 
        pts = 0
        board_len_in = board_length_ft * 12
        line_3, line_2, line_1 = 6, 12, 72
        
        for p in valid:
            if p.owner != leader_owner:
                # We reached an opponent's puck. 
                # If it's tied with the previous scoring pucks, they are disqualified.
                break 
            
            # Check if this puck is tied with the nearest opponent puck
            # (We find the first opponent puck to check for a tie)
            opponent_pucks = [op for op in valid if op.owner != leader_owner]
            if opponent_pucks and p.x_in == opponent_pucks[0].x_in:
                continue # This puck is tied with an opponent and doesn't count

            dist_end = board_len_in - p.x_in
            left_edge = dist_end + p.radius_in
            is_edging = (p.x_in + p.radius_in > board_len_in)
            
            if edging_enabled and is_edging: 
                pts += 4
            elif left_edge < line_3: pts += 3
            elif left_edge < line_2: pts += 2
            elif left_edge < line_1: pts += 1
            
        points[leader_owner] = pts
        self.round_points = points

    def commit_round(self, target_score):
        if self.game_winner:
            return self.game_winner, True

        self.p1_score += self.round_points[P1]
        self.p2_score += self.round_points[P2]
        
        round_winner = None
        if self.round_points[P2] > 0: round_winner = P2
        elif self.round_points[P1] > 0: round_winner = P1
        
        self.round_points = {P1: 0, P2: 0}
        
        if (self.p1_score >= target_score or self.p2_score >= target_score) and \
           (self.p1_score != self.p2_score):
            self.game_winner = P1 if self.p1_score > self.p2_score else P2
            return self.game_winner, True
            
        return round_winner, False

    def _draw_segment(self, screen, points, color):
        pygame.draw.polygon(screen, color, points)

    def _draw_digital_display(self, screen, x, y, value, size, color, thickness=3, force_two_digits=True):
        mapping = {
            '0': (1,0,1,1,1,1,1), '1': (0,0,0,0,0,1,1), '2': (1,1,1,0,1,1,0),
            '3': (1,1,1,0,0,1,1), '4': (0,1,0,1,0,1,1), '5': (1,1,1,1,0,0,1),
            '6': (1,1,1,1,1,0,1), '7': (1,0,0,0,0,1,1), '8': (1,1,1,1,1,1,1),
            '9': (1,1,1,1,0,1,1)
        }
        
        if value == 0 and not force_two_digits:
            return

        if force_two_digits:
            digits = f"{value:02d}"[-2:]
        else:
            digits = str(value)

        w, h = size, int(size * 1.9)
        spacing = size // 2
        off = thickness // 2

        for char in digits:
            segs = mapping.get(char, (0,0,0,0,0,0,0))
            segment_data = [
                [(x+off, y), (x+w-off, y), (x+w, y+off), (x+w-off, y+thickness), (x+off, y+thickness), (x, y+off)],
                [(x+off, y+h//2), (x+w-off, y+h//2), (x+w, y+h//2+off), (x+w-off, y+h//2+thickness), (x+off, y+h//2+thickness), (x, y+h//2+off)],
                [(x+off, y+h-thickness), (x+w-off, y+h-thickness), (x+w, y+h-off), (x+w-off, y+h), (x+off, y+h), (x, y+h-off)],
                [(x, y+off), (x+thickness, y+off+off), (x+thickness, y+h//2-off), (x+off, y+h//2), (x, y+h//2-off), (x, y+off)],
                [(x, y+h//2+off), (x+thickness, y+h//2+off+off), (x+thickness, y+h-off-off), (x+off, y+h-off), (x, y+h-off-off), (x, y+h//2+off)],
                [(x+w-thickness, y+off+off), (x+w, y+off), (x+w, y+h//2-off), (x+w-off, y+h//2), (x+w-thickness, y+h//2-off), (x+w-thickness, y+off+off)],
                [(x+w-thickness, y+h//2+off+off), (x+w, y+h//2+off), (x+w, y+h-off-off), (x+w-off, y+h-off), (x+w-thickness, y+h-off-off), (x+w-thickness, y+h//2+off+off)]
            ]

            for i, poly_pts in enumerate(segment_data):
                if segs[i]:
                    self._draw_segment(screen, poly_pts, color)
            x += w + spacing

    def draw(self, screen, screen_w, screen_h, throws_left, current_turn, p1_rgb, p2_rgb, is_moving, game_over=False):
        ppi = constants.PPI
        g_right = constants.GUTTER_PADDING_RIGHT
        
        box_w = int(21.0 * ppi) 
        box_h = int(12.0 * ppi)
        
        gutter_center_x = screen_w - (g_right // 2)
        box_rect = pygame.Rect(0, 0, box_w, box_h)
        box_rect.center = (gutter_center_x, screen_h // 2)

        thickness = max(2, int(0.3 * ppi)) 
        digit_size = int(1.75 * ppi)
        digit_spacing = digit_size // 2
        
        small_digit_size = int(0.75 * ppi)
        small_spacing = small_digit_size // 2
        
        dot_radius = int(0.4 * ppi)

        pygame.draw.rect(screen, BLACK, box_rect, border_radius=int(1.25 * ppi))
        pygame.draw.rect(screen, DARK_GREY, box_rect, width=2, border_radius=int(1.25 * ppi))
        pygame.draw.line(screen, (40, 40, 40), (box_rect.centerx, box_rect.top + int(1.25 * ppi)), 
                         (box_rect.centerx, box_rect.bottom - int(1.25 * ppi)), 1)

        p1_center = box_rect.left + (box_rect.width / 4)
        p2_center = box_rect.right - (box_rect.width / 4)

        line_w = int(1.5 * ppi)
        gap = int(0.5 * ppi)
        total_shot_w = (line_w * 4) + (gap * 3)
        
        p1_track_L = p1_center - (total_shot_w / 2)
        p1_track_R = p1_center + (total_shot_w / 2)
        p2_track_L = p2_center - (total_shot_w / 2)
        p2_track_R = p2_center + (total_shot_w / 2)

        score_y = box_rect.top + int(2.5 * ppi)
        main_score_w = (digit_size * 2) + digit_spacing
        
        self._draw_digital_display(screen, p1_center - (main_score_w / 2), score_y, self.p1_score, digit_size, p1_rgb, thickness=thickness, force_two_digits=True)
        self._draw_digital_display(screen, p2_center - (main_score_w / 2), score_y, self.p2_score, digit_size, p2_rgb, thickness=thickness, force_two_digits=True)

        round_y = score_y + int(4.5 * ppi)
        
        def draw_justified_info(track_L, track_R, player_id, rgb):
            show_dot = False
            if game_over:
                if self.game_winner == player_id:
                    if (time.time() % 1.0) < 0.5:
                        show_dot = True
            else:
                if (throws_left[player_id] > 0) and (current_turn == player_id) and (not is_moving):
                    show_dot = True

            if show_dot:
                padding = int(0.1 * ppi)
                dot_x = track_L + dot_radius + padding
                dot_y = round_y + int(0.7 * ppi)
                pygame.draw.circle(screen, WHITE, (int(dot_x), int(dot_y)), dot_radius)

            score_val = self.round_points[player_id]
            if score_val > 0:
                digits = str(score_val)
                score_w = (small_digit_size * len(digits)) + (small_spacing * (len(digits) - 1))
                start_x = track_R - score_w
                self._draw_digital_display(screen, start_x, round_y, score_val, small_digit_size, rgb, thickness=max(1, thickness//2), force_two_digits=False)

        draw_justified_info(p1_track_L, p1_track_R, P1, p1_rgb)
        draw_justified_info(p2_track_L, p2_track_R, P2, p2_rgb)

        tracker_y = box_rect.bottom - int(2.75 * ppi) 
        
        p1_celebrate = (game_over and self.game_winner == P1)
        p2_celebrate = (game_over and self.game_winner == P2)
        
        self.draw_shot_lines(screen, p1_track_L, throws_left[P1], p1_rgb, tracker_y, P1, p1_celebrate)
        self.draw_shot_lines(screen, p2_track_L, throws_left[P2], p2_rgb, tracker_y, P2, p2_celebrate)
        
    def draw_shot_lines(self, screen, start_x, shots_left, color, y_pos, player_id, celebrate):
        ppi = constants.PPI
        line_w = int(1.5 * ppi)
        line_h = int(0.4 * ppi)
        gap = int(0.5 * ppi)
        
        available_colors = list(PUCK_COLORS.values())
        now = time.time()
        
        used_shots = 4 - shots_left
        
        for i in range(4):
            x = start_x + (i * (line_w + gap))
            
            draw_color = color
            
            if celebrate:
                key = f"{player_id}_{i}"
                if key not in self.flash_timers or now > self.flash_timers[key]:
                    self.flash_colors[key] = random.choice(available_colors)
                    next_interval = random.gauss(1.0, 0.15)
                    self.flash_timers[key] = now + max(0.1, next_interval)
                
                draw_color = self.flash_colors[key]
            else:
                if i < used_shots:
                    draw_color = (25, 25, 25)
            
            pygame.draw.rect(screen, draw_color, (x, y_pos, line_w, line_h), border_radius=max(1, int(0.1 * ppi)))