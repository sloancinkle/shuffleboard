import pygame
import time
import sys
import os

from . import constants
from . import memory
from . import physics
from .input import InputHandler

from .components.options import Options
from .components.scoreboard import Scoreboard
from .components.board import Table, Gutter
from .components.puck import Puck 

from .constants import REAL_BOARD_WIDTH, FPS, WOOD_DARK, BLACK, \
                       FOUL_LINE_FT, DEFAULT_LENGTH_FT, DEFAULT_PUCK_SIZE, \
                       TABLE_FRICTION, GUTTER_FRICTION, THROW_LINE_FT, \
                       STATE_GUTTER, STATE_THROWN, STATE_ON_BOARD, STATE_SELECTED, STATE_READY, \
                       P1, P2, PUCK_COLORS, SCORE_GAP_IN

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
        base_path = os.path.join(base_path, 'assets')
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
    return os.path.join(base_path, relative_path)

def force_update_ppi(new_ppi):
    constants.PPI = new_ppi
    constants.GUTTER_PADDING_LEFT = int(constants.GUTTER_LEFT_IN * new_ppi)
    constants.GUTTER_PADDING_RIGHT = int(constants.GUTTER_RIGHT_IN * new_ppi)
    constants.GUTTER_PADDING_Y = int(constants.GUTTER_Y_IN * new_ppi)
    constants.ICON_SIZE_PX = int(constants.ICON_SIZE_IN * new_ppi)

class Shuffleboard:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Shuffleboard")

        try:
            icon_path = resource_path("app_icon.png")
            pygame_icon = pygame.image.load(icon_path)
            pygame.display.set_icon(pygame_icon)
        except:
            pass

        self.clock = pygame.time.Clock()
        
        self.board_length_ft = DEFAULT_LENGTH_FT
        self.puck_size = DEFAULT_PUCK_SIZE
        
        saved_data = memory.load_memory()
        valid_save = bool(saved_data and "gameplay" in saved_data and "settings" in saved_data)

        self.menu = Options(self.board_length_ft, self.puck_size) 
        self.scoreboard = Scoreboard()
        self.gutter = Gutter(self.puck_size)
        self.input = InputHandler()

        if valid_save:
            s = saved_data.get("settings", {})
            self.board_length_ft = s.get("length", DEFAULT_LENGTH_FT)
            self.puck_size = s.get("puck_size", DEFAULT_PUCK_SIZE)
            
            saved_w = s.get("window_width", 1000)
            saved_h = s.get("window_height", 600)
            self.screen = pygame.display.set_mode((saved_w, saved_h), pygame.RESIZABLE)
            
            # Now safe to call: menu, scoreboard, and gutter all exist
            self.update_dimensions(saved_w, saved_h)
            
            self.table = Table(self.screen_w, self.screen_h, self.surface_rect, self.board_length_ft)
            self.scoreboard = Scoreboard()
            self.scoreboard.reset()
            self.gutter = Gutter(self.puck_size)
            self.input = InputHandler()

            self.menu.target_score = s.get("target_score", 21)
            self.menu.edging_enabled = s.get("edging", True)
            self.menu.p1_color = s.get("p1_color_name", "Red")
            self.menu.p2_color = s.get("p2_color_name", "Blue")
            self.menu.refresh_puck_positions() 

            g = saved_data.get("gameplay", {})
            self.current_turn = g.get("current_turn", P1)
            self.round_winner = g.get("round_winner", P1)
            self.throws_left = {
                P1: g.get("throws_left_p1", 4), 
                P2: g.get("throws_left_p2", 4)
            }
            self.game_over = g.get("game_over", False)
            self.game_state = g.get("game_state", "AIMING")
            self.state = "GAME"
            
            if g.get("state_timer_active", False):
                self.state_timer = time.time()
            else:
                self.state_timer = 0

            sc = saved_data.get("scores", {})
            self.scoreboard.p1_score = sc.get("p1_score", 0)
            self.scoreboard.p2_score = sc.get("p2_score", 0)
            self.scoreboard.round_points = {
                P1: sc.get("round_p1", 0), 
                P2: sc.get("round_p2", 0)
            }
            self.scoreboard.game_winner = sc.get("game_winner", None)

            self.gutter.pucks = []
            for p_data in saved_data.get("pucks", []):
                col = tuple(p_data.get("color", PUCK_COLORS["Red"]))
                owner = p_data.get("owner", P1)
                new_puck = Puck(owner, self.puck_size, col, 
                                font="couriernew", text_color=BLACK)
                new_puck.x_in = p_data.get("x_in", 0)
                new_puck.y_in = p_data.get("y_in", 0)
                new_puck.state = p_data.get("state", STATE_GUTTER)
                
                new_puck.dx = p_data.get("dx", 0)
                new_puck.dy = p_data.get("dy", 0)
                new_puck.is_moving = p_data.get("is_moving", False)
                
                self.gutter.add_puck(new_puck)

        else:
            self.screen = pygame.display.set_mode((1000, 600), pygame.RESIZABLE)
            self.update_dimensions()
            self.table = Table(self.screen_w, self.screen_h, self.surface_rect, self.board_length_ft)
            self.round_winner = P1
            self.throws_left = {P1: 4, P2: 4}
            self.game_over = False
            self.start_new_round()

    def update_dimensions(self, new_w=None, new_h=None):
        if new_w and new_h:
            self.screen_w, self.screen_h = new_w, new_h
        else:
            self.screen_w, self.screen_h = self.screen.get_size()

        # Internal layout units in inches
        board_in_w = self.board_length_ft * 12
        scoreboard_in_w = 21.0      
        
        # Combined unit width: Gutter + Table + Gap + Scoreboard + Gutter
        total_content_in_w = (constants.GUTTER_LEFT_IN + board_in_w + 
                             constants.SCORE_GAP_IN + scoreboard_in_w + 
                             constants.GUTTER_RIGHT_IN)
        total_content_in_h = constants.REAL_BOARD_WIDTH + (constants.GUTTER_Y_IN * 2)

        # Calculate Max PPI to fit the unit
        new_ppi = min(self.screen_w / total_content_in_w, self.screen_h / total_content_in_h)
        force_update_ppi(new_ppi)

        # Horizontal centering offset for the entire unit
        offset_x = (self.screen_w - (total_content_in_w * new_ppi)) / 2
        offset_y = (self.screen_h - (total_content_in_h * new_ppi)) / 2

        # Update Table and Gutter boundaries based on centering
        constants.GUTTER_PADDING_LEFT = int((constants.GUTTER_LEFT_IN * new_ppi) + offset_x)
        constants.GUTTER_PADDING_Y = int((constants.GUTTER_Y_IN * new_ppi) + offset_y)
        
        scoreboard_area_px = (constants.SCORE_GAP_IN + scoreboard_in_w + 
                              constants.GUTTER_RIGHT_IN) * new_ppi
        constants.GUTTER_PADDING_RIGHT = int(scoreboard_area_px + offset_x)

        self.board_length_px = board_in_w * new_ppi
        self.surface_rect = pygame.Rect(
            constants.GUTTER_PADDING_LEFT, 
            constants.GUTTER_PADDING_Y, 
            self.board_length_px, 
            constants.REAL_BOARD_WIDTH * new_ppi
        )
        
        # Now call the method to update the UI icons and Table
        self._update_ui_elements()
        self.table = Table(self.screen_w, self.screen_h, self.surface_rect, self.board_length_ft)
        self._update_all_pucks_visuals()

    def _update_ui_elements(self):
        # Set a fixed size that never changes (e.g., 2.5 inches at a standard 10 PPI)
        STATIC_PPI = 10.0 
        icon_dim = int(constants.ICON_SIZE_IN * STATIC_PPI)
        
        # Use the static_dim for icon loading, NOT constants.ICON_SIZE_PX
        self.icons = {
            'menu_grey': self.load_colored_icon(resource_path("menu-icon.png"), constants.GREY, (icon_dim, icon_dim)),
            'menu_white': self.load_colored_icon(resource_path("menu-icon.png"), constants.WHITE, (icon_dim, icon_dim)),
            'replay_grey': self.load_colored_icon(resource_path("replay-icon.png"), constants.GREY, (icon_dim, icon_dim)),
            'replay_white': self.load_colored_icon(resource_path("replay-icon.png"), constants.WHITE, (icon_dim, icon_dim)),
            'puck_grey': self.load_colored_icon(resource_path("puck_icon.png"), constants.GREY, (icon_dim, icon_dim)),
            'puck_white': self.load_colored_icon(resource_path("puck_icon.png"), constants.WHITE, (icon_dim, icon_dim))
        }

        fixed_gap = 12 
        margin = 15 
        
        self.icon_rect = pygame.Rect(0, 0, icon_dim, icon_dim)
        self.icon_rect.topright = (self.screen_w - margin, margin)
        
        self.reset_btn_rect = pygame.Rect(0, 0, icon_dim, icon_dim)
        self.reset_btn_rect.topright = (self.icon_rect.left - fixed_gap, margin)
        
        self.puck_btn_rect = pygame.Rect(0, 0, icon_dim, icon_dim)
        self.puck_btn_rect.topright = (self.reset_btn_rect.left - fixed_gap, margin)

    def load_colored_icon(self, filename, color, size):
        try:
            image = pygame.image.load(filename).convert_alpha()
            image = pygame.transform.smoothscale(image, size)
            r, g, b = color[0], color[1], color[2]
            color_surf = pygame.Surface(size, pygame.SRCALPHA)
            color_surf.fill((r, g, b, 0)) 
            image.blit(color_surf, (0, 0), special_flags=pygame.BLEND_ADD)
            return image
        except FileNotFoundError:
            fallback = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(fallback, color, (0,0,size[0],size[1]))
            return fallback

    def start_new_round(self):
        self.state = "GAME" 
        self.game_state = "AIMING"
        self.throws_left = {P1: 4, P2: 4}
        self.game_over = False
        
        self.gutter.pucks = []
        first = self.round_winner
        second = P2 if first == P1 else P1
        c1 = PUCK_COLORS[self.menu.p1_color]
        c2 = PUCK_COLORS[self.menu.p2_color]
        
        for _ in range(4):
            p_sec = Puck(second, self.puck_size, c2 if second == P2 else c1, 
                         font="couriernew", text_color=BLACK)
            p_fir = Puck(first, self.puck_size, c1 if first == P1 else c2, 
                         font="couriernew", text_color=BLACK)
            self.gutter.add_puck(p_sec)
            self.gutter.add_puck(p_fir)
            
        self.gutter.scatter_pucks(self.screen_h)
        self.current_turn = self.round_winner
        self.state_timer = 0
        self.input.reset()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    running = False
                    memory.save_memory(self) 
                self.handle_events(event)
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def apply_hard_constraints(self, w, h):
        min_ppi = 7.0
        board_in_w = self.board_length_ft * 12
        scoreboard_in_w = 21.0
        gap_in = constants.SCORE_GAP_IN
        
        total_in_w = (constants.GUTTER_LEFT_IN + board_in_w + 
                    gap_in + scoreboard_in_w + constants.GUTTER_RIGHT_IN)
        total_in_h = constants.REAL_BOARD_WIDTH + (constants.GUTTER_Y_IN * 2)
        
        min_w = int(total_in_w * min_ppi)
        min_h = int(total_in_h * min_ppi) # Fixed variable name

        if w < min_w or h < min_h:
            w, h = max(w, min_w), max(h, min_h)
            self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
            
        return w, h

    def handle_events(self, event):
        if event.type == pygame.VIDEORESIZE:
            # 1. Enforce the 7 PPI limit immediately
            new_w, new_h = self.apply_hard_constraints(event.w, event.h)
            
            # 2. Update all internal PPI and centering math
            self.update_dimensions(new_w, new_h)
            
            # 3. Refresh the table object
            self.table = Table(self.screen_w, self.screen_h, self.surface_rect, self.board_length_ft)
            
            # 4. If in Menu, update its unique layout
            if self.state == "MENU":
                self.menu.update_layout(self.screen_w, self.screen_h)
                
            # 5. TRIGGER LIVE REDRAW: This is what stops the "stretching" look
            self.draw()
            pygame.display.flip()
            return
        
        if self.state == "MENU":
            result = self.menu.handle_event(event)
            
            if result == "RESIZE":
                force_update_ppi(self.menu.ppi)
                self.update_dimensions()
                self.menu.update_layout(self.screen_w, self.screen_h) 
                self.table = Table(self.screen_w, self.screen_h, self.surface_rect, self.board_length_ft)
                self._update_all_pucks_visuals()

            elif result == "SLIDER_UPDATE":
                self.board_length_ft = int(self.menu.length)
                self.update_dimensions()
                self.menu.update_layout(self.screen_w, self.screen_h)
                self.table = Table(self.screen_w, self.screen_h, self.surface_rect, self.board_length_ft)
                self._update_all_pucks_visuals()

            elif result == "START":
                memory.save_memory(self)
                self.state = "GAME"
                # UPDATED: Use new edging_enabled property name
                has_changed = (int(self.menu.length) != int(self.menu.orig_length)) or \
                              (self.menu.puck_size != self.menu.orig_puck_size) or \
                              (self.menu.edging_enabled != self.menu.orig_edging) or \
                              (self.menu.target_score != self.menu.orig_target)
                
                if has_changed:
                    self.board_length_ft = int(self.menu.length)
                    self.puck_size = self.menu.puck_size
                    self.scoreboard.reset()
                    self.round_winner = P1
                    self.start_new_round()
                else:
                    self._update_all_pucks_visuals()

                gap = int(1.25 * constants.PPI)
                self.icon_rect.topright = (self.screen_w - int(1.8 * constants.PPI), int(1.25 * constants.PPI))
                self.reset_btn_rect.topright = (self.icon_rect.left - gap, int(1.25 * constants.PPI))
                self.puck_btn_rect.topright = (self.reset_btn_rect.left - gap, int(1.25 * constants.PPI))
            else:
                self._update_all_pucks_visuals()

        elif self.state == "GAME":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.icon_rect.collidepoint(event.pos):
                    self.state = "MENU"
                    self.menu.set_initials(self.board_length_ft, self.puck_size, self.menu.target_score)
                    self.menu.update_layout(self.screen_w, self.screen_h)
                    return
                if self.reset_btn_rect.collidepoint(event.pos):
                    self.reset_game()
                    return
                if self.puck_btn_rect.collidepoint(event.pos):
                    self.reset_non_scoring_pucks()
                    return

            self.input.handle_input(event, self)

    def _update_all_pucks_visuals(self):
        """Forces all pucks to recalculate their pixel radius based on the new PPI."""
        c1 = PUCK_COLORS[self.menu.p1_color]
        c2 = PUCK_COLORS[self.menu.p2_color]
        
        for p in self.gutter.pucks:
            color = c1 if p.owner == P1 else c2
            p.update_visuals(self.puck_size, color)

    def reset_game(self):
        self.scoreboard.reset()
        self.round_winner = P1
        self.start_new_round()

    def reset_non_scoring_pucks(self):
        if self.game_over:
            for p in self.gutter.pucks:
                p.state = STATE_GUTTER
                p.dx = 0
                p.dy = 0
                p.is_moving = False
                p.is_selected = False
            self.input.selected_puck = None
            self.gutter.scatter_pucks(self.screen_h)
        else:
            active_pucks = []
            reset_candidates = []
            for p in self.gutter.pucks:
                if p.state in (STATE_ON_BOARD, STATE_THROWN, STATE_SELECTED):
                    active_pucks.append(p)
                else:
                    p.state = STATE_GUTTER
                    p.dx = 0; p.dy = 0
                    p.is_moving = False
                    reset_candidates.append(p)
            self.gutter.pucks = reset_candidates
            self.gutter.scatter_pucks(self.screen_h)
            self.gutter.pucks.extend(active_pucks)

    def shoot_puck(self, puck, dx, dy, count_throw=True):
        puck.dx = dx; puck.dy = dy
        puck.is_moving = True
        puck.is_selected = False
        
        self.input.selected_puck = None
        
        if count_throw:
            puck.state = STATE_THROWN
            if not self.game_over:
                if self.throws_left[puck.owner] > 0: self.throws_left[puck.owner] -= 1
            self.game_state = "MOVING"
        else:
            if self.table.is_touching_table(puck):
                puck.state = STATE_THROWN
            else:
                puck.state = STATE_GUTTER 

    def update(self):
        if self.state == "GAME":
            self.gutter.free_play = self.game_over
            self.input.update_hover(self)
            
            current_ppi = constants.PPI 
            g_left_px = constants.GUTTER_PADDING_LEFT
            g_y_px = constants.GUTTER_PADDING_Y
            
            b_min_x = -g_left_px / current_ppi
            b_max_x = (self.screen_w - g_left_px) / current_ppi
            b_min_y = -g_y_px / current_ppi
            b_max_y = (self.screen_h - g_y_px) / current_ppi

            board_len_in = (self.screen_w - g_left_px - constants.GUTTER_PADDING_RIGHT) / current_ppi
            throw_line_in = THROW_LINE_FT * 12
            
            all_pucks = self.gutter.pucks
            moving_count = 0
            
            for puck in all_pucks:
                if self.game_over:
                     if puck.state == STATE_READY:
                         puck.state = STATE_ON_BOARD
                     if puck.state == STATE_THROWN and not puck.is_moving:
                         puck.state = STATE_ON_BOARD

                if puck.state in [STATE_THROWN, STATE_ON_BOARD, STATE_READY]:
                    if not self.table.is_puck_stable(puck): puck.state = STATE_GUTTER
                
                if puck.is_moving:
                    if self.game_over:
                        on_wood = self.table.is_touching_table(puck)
                        fric = TABLE_FRICTION if on_wood else GUTTER_FRICTION
                    else:
                        fric = TABLE_FRICTION if (puck.state in [STATE_THROWN, STATE_ON_BOARD, STATE_READY]) else GUTTER_FRICTION

                    is_still_moving = physics.update_puck_movement(puck, fric)
                    
                    if is_still_moving:
                        physics.resolve_boundary_bounce(puck, b_min_x, b_max_x, b_min_y, b_max_y)

                        if puck.state == STATE_GUTTER:
                            self.gutter.resolve_rect_obstacle(puck, 0, board_len_in, 0, REAL_BOARD_WIDTH)
                        elif puck.state in (STATE_READY, STATE_SELECTED):
                             if not self.game_over:
                                self.gutter.resolve_rect_obstacle(puck, throw_line_in, board_len_in, 0, REAL_BOARD_WIDTH)

                    if puck.state in (STATE_THROWN, STATE_ON_BOARD): moving_count += 1

                if puck.state == STATE_GUTTER:
                    self.gutter.resolve_rect_obstacle(puck, 0, board_len_in, 0, REAL_BOARD_WIDTH)

            for i in range(len(all_pucks)):
                p1 = all_pucks[i]
                for j in range(i+1, len(all_pucks)):
                    p2 = all_pucks[j]
                    
                    should_collide = False
                    
                    if p1.state == STATE_GUTTER and p2.state == STATE_GUTTER:
                        should_collide = True
                    
                    elif self.game_over:
                        s1_on_table = p1.state != STATE_GUTTER
                        s2_on_table = p2.state != STATE_GUTTER
                        
                        if s1_on_table and s2_on_table:
                             should_collide = True

                    else:
                        valid_states = [STATE_THROWN, STATE_ON_BOARD, STATE_READY, STATE_SELECTED]
                        if p1.state in valid_states and p2.state in valid_states:
                             if p1.state == STATE_SELECTED and p2.state == STATE_ON_BOARD: pass
                             elif p2.state == STATE_SELECTED and p1.state == STATE_ON_BOARD: pass
                             else: should_collide = True
                    
                    if should_collide:
                        physics.check_puck_collision(p1, p2)

            for puck in self.gutter.pucks:
                # Calculate screen-relative bounds in inches
                # Screen bounds relative to surface_rect (0,0)
                min_x = -constants.GUTTER_PADDING_LEFT / constants.PPI
                max_x = (self.screen_w - constants.GUTTER_PADDING_LEFT) / constants.PPI
                min_y = -constants.GUTTER_PADDING_Y / constants.PPI
                max_y = (self.screen_h - constants.GUTTER_PADDING_Y) / constants.PPI

                # Clamp x and y based on radius to keep puck fully on screen
                if puck.x_in < min_x + puck.radius_in:
                    puck.x_in = min_x + puck.radius_in
                    puck.dx = 0 # Optional: stop velocity if it hits the "window wall"
                elif puck.x_in > max_x - puck.radius_in:
                    puck.x_in = max_x - puck.radius_in
                    puck.dx = 0

                if puck.y_in < min_y + puck.radius_in:
                    puck.y_in = min_y + puck.radius_in
                    puck.dy = 0
                elif puck.y_in > max_y - puck.radius_in:
                    puck.y_in = max_y - puck.radius_in
                    puck.dy = 0

            scoring_candidates = [p for p in all_pucks if self.table.is_touching_table(p)]
            self.scoreboard.calculate_points(scoring_candidates, self.board_length_ft, self.menu.edging_enabled, self.game_over)

            if self.game_state == "MOVING" and moving_count == 0: self.handle_turn_end()
            if self.game_state == "ROUND_OVER_DELAY":
                if self.game_over or (time.time() - self.state_timer > 2.0):
                    winner, is_game_over = self.scoreboard.commit_round(self.menu.target_score)
                    if is_game_over:
                        self.game_over = True; self.round_winner = winner; self.game_state = "AIMING"
                        memory.save_memory(self)
                    else:
                        self.round_winner = winner if winner else (P2 if self.round_winner == P1 else P1)
                        self.start_new_round()

    def handle_turn_end(self):
        f_line = (self.board_length_ft - FOUL_LINE_FT) * 12
        
        for p in self.gutter.pucks:
            if p.state in (STATE_THROWN, STATE_ON_BOARD, STATE_READY):
                if self.game_over:
                    p.state = STATE_ON_BOARD
                else:
                    has_crossed = (p.x_in - p.radius_in) > f_line
                    
                    if has_crossed:
                        p.state = STATE_ON_BOARD
                    else:
                        p.state = STATE_GUTTER
                        self.gutter.place_puck_nearest(p, self.screen_h, self.screen_w)

        if self.throws_left[P1] == 0 and self.throws_left[P2] == 0:
            self.game_state = "ROUND_OVER_DELAY"
            self.state_timer = time.time()
        else:
            if not self.game_over:
                next_turn = P2 if self.current_turn == P1 else P1
                if self.throws_left[next_turn] > 0: self.current_turn = next_turn
            self.game_state = "AIMING"
        
        memory.save_memory(self)

    def draw(self):
        if self.state == "MENU":
            self.menu.draw(self.screen)
        else:
            self.screen.fill(WOOD_DARK)
            c1, c2 = PUCK_COLORS[self.menu.p1_color], PUCK_COLORS[self.menu.p2_color]
            
            self.scoreboard.draw(
                self.screen, self.screen_w, self.screen_h, 
                self.throws_left, self.current_turn, c1, c2, 
                self.game_state == "MOVING", self.game_over,
                self.board_length_px
            )

            self.gutter.draw_gutter_layer(self.screen)

            shadow_offset = 4 
            shadow_surface = pygame.Surface((self.surface_rect.width, self.surface_rect.height), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 60)) 
            self.screen.blit(shadow_surface, (self.surface_rect.x + shadow_offset, self.surface_rect.y + shadow_offset))
            
            self.table.draw(self.screen)
            
            self.gutter.draw_puck_shadows(self.screen, self.surface_rect, [STATE_SELECTED, STATE_READY, STATE_THROWN])
            self.gutter.draw_active_layer(self.screen)
            
            self.gutter.draw_puck_shadows(self.screen, self.surface_rect, [STATE_ON_BOARD])
            self.gutter.draw_edging_layer(self.screen)
            
            m_pos = pygame.mouse.get_pos()
            
            k_m = 'menu_white' if self.icon_rect.collidepoint(m_pos) else 'menu_grey'
            self.screen.blit(self.icons[k_m], self.icon_rect)
            
            k_r = 'replay_white' if self.reset_btn_rect.collidepoint(m_pos) else 'replay_grey'
            self.screen.blit(self.icons[k_r], self.reset_btn_rect)
            
            k_p = 'puck_white' if self.puck_btn_rect.collidepoint(m_pos) else 'puck_grey'
            self.screen.blit(self.icons[k_p], self.puck_btn_rect)