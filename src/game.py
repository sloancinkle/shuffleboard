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
from .components.table import Table, Gutter
from .components.puck import Puck 

from .constants import REAL_BOARD_WIDTH, FPS, WOOD_DARK, WHITE, GREY, BLACK, \
                       FOUL_LINE_FT, DEFAULT_LENGTH_FT, DEFAULT_PUCK_SIZE, \
                       TABLE_FRICTION, GUTTER_FRICTION, THROW_LINE_FT, \
                       STATE_GUTTER, STATE_THROWN, STATE_ON_BOARD, STATE_SELECTED, STATE_READY, \
                       P1, P2, PUCK_COLORS

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
        
        # --- FIX: Check for "gameplay" key to ensure save file is compatible ---
        valid_save = False
        if saved_data and "gameplay" in saved_data and "settings" in saved_data:
            valid_save = True

        if valid_save:
            s = saved_data["settings"]
            self.board_length_ft = s["length"]
            self.puck_size = s["puck_size"]
            saved_ppi = s["ppi"]
            
            force_update_ppi(saved_ppi)
            self.update_dimensions()
            
            self.table = Table(self.screen_w, self.screen_h, self.surface_rect)
            self.scoreboard = Scoreboard()
            self.scoreboard.reset()
            self.gutter = Gutter(self.puck_size)
            self.input = InputHandler()
            self.menu = Options(self.board_length_ft, self.puck_size)
            
            self.menu.ppi = saved_ppi
            self.menu.target_score = s["target_score"]
            self.menu.hangers_enabled = s["hangers"]
            self.menu.p1_color = s["p1_color_name"]
            self.menu.p2_color = s["p2_color_name"]
            self.menu.refresh_puck_positions() 

            g = saved_data["gameplay"]
            self.current_turn = g["current_turn"]
            self.round_winner = g["round_winner"]
            self.throws_left = {P1: g["throws_left_p1"], P2: g["throws_left_p2"]}
            self.game_over = g["game_over"]
            self.game_state = g["game_state"]
            self.state = "GAME"
            
            if g.get("state_timer_active", False):
                self.state_timer = time.time()
            else:
                self.state_timer = 0

            sc = saved_data["scores"]
            self.scoreboard.p1_score = sc["p1_score"]
            self.scoreboard.p2_score = sc["p2_score"]
            self.scoreboard.round_points = {P1: sc["round_p1"], P2: sc["round_p2"]}
            self.scoreboard.game_winner = sc["game_winner"]

            self.gutter.pucks = []
            for p_data in saved_data["pucks"]:
                col = tuple(p_data["color"]) 
                new_puck = Puck(p_data["owner"], self.puck_size, col, 
                                font="couriernew", text_color=BLACK)
                new_puck.x_in = p_data["x_in"]
                new_puck.y_in = p_data["y_in"]
                new_puck.state = p_data["state"]
                
                new_puck.dx = p_data.get("dx", 0)
                new_puck.dy = p_data.get("dy", 0)
                new_puck.is_moving = p_data.get("is_moving", False)
                
                self.gutter.add_puck(new_puck)

        else:
            self.update_dimensions()
            self.table = Table(self.screen_w, self.screen_h, self.surface_rect)
            self.scoreboard = Scoreboard()
            self.gutter = Gutter(self.puck_size)
            self.input = InputHandler()
            self.menu = Options(self.board_length_ft, self.puck_size)
            self.round_winner = P1 
            self.throws_left = {P1: 4, P2: 4}
            self.game_over = False
            self.start_new_round()

    def update_dimensions(self):
        current_ppi = constants.PPI 
        g_left = constants.GUTTER_PADDING_LEFT
        g_right = constants.GUTTER_PADDING_RIGHT
        g_y = constants.GUTTER_PADDING_Y

        self.board_length_px = self.board_length_ft * 12 * current_ppi 
        self.screen_w = int(g_left + self.board_length_px + g_right)
        self.screen_h = int((REAL_BOARD_WIDTH * current_ppi) + (g_y * 2))
        
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption(f"Shuffleboard")
        
        self.surface_rect = pygame.Rect(
            g_left, g_y, 
            self.board_length_px, REAL_BOARD_WIDTH * current_ppi
        )

        icon_dim = constants.ICON_SIZE_PX
        self.icon_rect = pygame.Rect(0, 0, icon_dim, icon_dim)
        self.reset_btn_rect = pygame.Rect(0, 0, icon_dim, icon_dim)
        
        self.icons = {
            'menu_grey': self.load_colored_icon(resource_path("menu-icon.png"), GREY, (icon_dim, icon_dim)),
            'menu_white': self.load_colored_icon(resource_path("menu-icon.png"), WHITE, (icon_dim, icon_dim)),
            'replay_grey': self.load_colored_icon(resource_path("replay-icon.png"), GREY, (icon_dim, icon_dim)),
            'replay_white': self.load_colored_icon(resource_path("replay-icon.png"), WHITE, (icon_dim, icon_dim))
        }
        
        self.icon_rect.topright = (self.screen_w - int(1.8 * current_ppi), int(1.25 * current_ppi))
        self.reset_btn_rect.topright = (self.icon_rect.left - int(1.25 * current_ppi), int(1.25 * current_ppi))

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

    def handle_events(self, event):
        if self.state == "MENU":
            result = self.menu.handle_event(event)
            
            if result == "RESIZE":
                force_update_ppi(self.menu.ppi)
                self.update_dimensions()
                self.menu.update_layout(self.screen_w, self.screen_h) 
                self.table = Table(self.screen_w, self.screen_h, self.surface_rect)
                self._update_all_pucks_visuals()

            elif result == "SLIDER_UPDATE":
                self.board_length_ft = int(self.menu.length)
                self.update_dimensions()
                self.menu.update_layout(self.screen_w, self.screen_h)
                self.table = Table(self.screen_w, self.screen_h, self.surface_rect)
                self._update_all_pucks_visuals()

            elif result == "START":
                memory.save_memory(self)
                self.state = "GAME"
                has_changed = (int(self.menu.length) != int(self.menu.orig_length)) or \
                              (self.menu.puck_size != self.menu.orig_puck_size) or \
                              (self.menu.hangers_enabled != self.menu.orig_hangers) or \
                              (self.menu.target_score != self.menu.orig_target)
                
                if has_changed:
                    self.board_length_ft = int(self.menu.length)
                    self.puck_size = self.menu.puck_size
                    self.scoreboard.reset()
                    self.start_new_round()
                else:
                    self._update_all_pucks_visuals()

                self.icon_rect.topright = (self.screen_w - int(1.8 * constants.PPI), int(1.25 * constants.PPI))
                self.reset_btn_rect.topright = (self.icon_rect.left - int(1.25 * constants.PPI), int(1.25 * constants.PPI))
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
            if self.game_over:
                self.handle_free_play_input(event)
            else:
                self.input.handle_input(event, self)

    def _update_all_pucks_visuals(self):
        c1 = PUCK_COLORS[self.menu.p1_color]
        c2 = PUCK_COLORS[self.menu.p2_color]
        
        for p in self.gutter.pucks:
            color = c1 if p.owner == P1 else c2
            p.update_visuals(self.menu.puck_size, color)
            p.font_name = "couriernew"
            p.text_color = BLACK

    def handle_free_play_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            m_pos = pygame.mouse.get_pos()
            for i in range(len(self.gutter.pucks) - 1, -1, -1):
                puck = self.gutter.pucks[i]
                if puck.state in (STATE_GUTTER, STATE_READY):
                    if puck.get_screen_pos().distance_to(m_pos) < puck.radius_px:
                        self.input.selected_puck = puck
                        puck.state = STATE_SELECTED
                        puck.is_selected = True
                        self.gutter.pucks.append(self.gutter.pucks.pop(i))
                        break
        else:
            self.input.handle_input(event, self)

    def reset_game(self):
        self.scoreboard.reset()
        self.round_winner = P1
        self.start_new_round()

    def shoot_puck(self, puck, dx, dy):
        puck.dx = dx; puck.dy = dy
        puck.is_moving = True
        puck.state = STATE_THROWN
        puck.is_selected = False
        if not self.game_over:
            if self.throws_left[puck.owner] > 0: self.throws_left[puck.owner] -= 1
        self.input.selected_puck = None
        self.game_state = "MOVING"

    def update(self):
        if self.state == "GAME":
            self.input.update_hover(self)
            current_ppi = constants.PPI 
            g_left_px = constants.GUTTER_PADDING_LEFT
            g_y_px = constants.GUTTER_PADDING_Y
            
            b_min_x = -g_left_px / current_ppi
            b_max_x = (self.screen_w - g_left_px) / current_ppi
            b_min_y = -g_y_px / current_ppi
            b_max_y = (self.screen_h - g_y_px) / current_ppi
            screen_bounds = (b_min_x, b_max_x, b_min_y, b_max_y)

            board_len_in = (self.screen_w - g_left_px - constants.GUTTER_PADDING_RIGHT) / current_ppi
            throw_line_in = THROW_LINE_FT * 12
            
            all_pucks = self.gutter.pucks
            moving_count = 0
            
            for puck in all_pucks:
                if puck.state in [STATE_THROWN, STATE_ON_BOARD, STATE_READY]:
                    if not self.table.is_puck_stable(puck): puck.state = STATE_GUTTER
                
                if puck.is_moving:
                    fric = TABLE_FRICTION if (puck.state in [STATE_THROWN, STATE_ON_BOARD, STATE_READY]) else GUTTER_FRICTION
                    is_still_moving = physics.update_puck_movement(puck, fric)
                    
                    if is_still_moving:
                        physics.resolve_boundary_bounce(puck, b_min_x, b_max_x, b_min_y, b_max_y)

                        if puck.state == STATE_GUTTER:
                            self.gutter.resolve_rect_obstacle(puck, 0, board_len_in, 0, REAL_BOARD_WIDTH)
                        elif puck.state in (STATE_READY, STATE_SELECTED):
                             self.gutter.resolve_rect_obstacle(puck, throw_line_in, board_len_in, 0, REAL_BOARD_WIDTH)

                    if puck.state in (STATE_THROWN, STATE_ON_BOARD): moving_count += 1

            for i in range(len(all_pucks)):
                p1 = all_pucks[i]
                for j in range(i+1, len(all_pucks)):
                    p2 = all_pucks[j]
                    valid_states = [STATE_THROWN, STATE_ON_BOARD, STATE_READY, STATE_SELECTED]
                    if p1.state in valid_states and p2.state in valid_states:
                        
                        if p1.state == STATE_SELECTED and p2.state == STATE_ON_BOARD: continue
                        if p2.state == STATE_SELECTED and p1.state == STATE_ON_BOARD: continue
                        
                        physics.check_puck_collision(p1, p2)

            scoring_candidates = [p for p in all_pucks if self.table.is_touching_table(p)]
            self.scoreboard.calculate_points(scoring_candidates, self.board_length_ft, self.menu.hangers_enabled)

            if self.game_state == "MOVING" and moving_count == 0: self.handle_turn_end()
            if self.game_state == "ROUND_OVER_DELAY":
                if self.game_over or (time.time() - self.state_timer > 2.0):
                    winner, is_game_over = self.scoreboard.commit_round(self.menu.target_score)
                    if is_game_over:
                        self.game_over = True; self.round_winner = winner; self.game_state = "AIMING"
                    else:
                        self.round_winner = winner if winner else (P2 if self.round_winner == P1 else P1)
                        self.start_new_round()

    def handle_turn_end(self):
        t_line = THROW_LINE_FT * 12
        f_line = (self.board_length_ft - FOUL_LINE_FT) * 12
        for p in self.gutter.pucks:
            if p.state == STATE_THROWN:
                if p.x_in < t_line: p.state = STATE_READY
                elif p.x_in < f_line:
                    p.state = STATE_GUTTER
                    self.gutter.place_puck_nearest(p, self.screen_h, self.screen_w)
                else: p.state = STATE_ON_BOARD
            elif p.state == STATE_ON_BOARD and p.x_in < f_line:
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
            self.scoreboard.draw(self.screen, self.screen_w, self.screen_h, self.throws_left, self.current_turn, c1, c2, self.game_state == "MOVING")
            self.gutter.draw_gutter_layer(self.screen)
            shadow_offset = 4 
            shadow_surface = pygame.Surface((self.surface_rect.width, self.surface_rect.height), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 60)) 
            self.screen.blit(shadow_surface, (self.surface_rect.x + shadow_offset, self.surface_rect.y + shadow_offset))
            self.table.draw(self.screen)
            self.gutter.draw_active_layer(self.screen)
            self.gutter.draw_hanging_layer(self.screen)
            m_pos = pygame.mouse.get_pos()
            k_m = 'menu_white' if self.icon_rect.collidepoint(m_pos) else 'menu_grey'
            self.screen.blit(self.icons[k_m], self.icon_rect)
            k_r = 'replay_white' if self.reset_btn_rect.collidepoint(m_pos) else 'replay_grey'
            self.screen.blit(self.icons[k_r], self.reset_btn_rect)