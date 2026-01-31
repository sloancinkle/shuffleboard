import pygame
import math
from . import constants
from .constants import THROW_LINE_FT, MAX_POWER, \
                       STATE_GUTTER, STATE_SELECTED, STATE_READY

class InputHandler:
    def __init__(self):
        self.selected_puck = None
        self.throw_history = []
    
    def reset(self):
        self.selected_puck = None
        self.throw_history = []

    def handle_input(self, event, game):
        if game.game_state != "AIMING":
            return

        ppi = constants.PPI
        control_limit_screen_x = game.surface_rect.left + (THROW_LINE_FT * 12 * ppi)

        if event.type == pygame.MOUSEBUTTONDOWN:
            m_pos = pygame.mouse.get_pos()
            
            if not game.game_over:
                if game.throws_left[game.current_turn] <= 0:
                    return

            for i in range(len(game.gutter.pucks) - 1, -1, -1):
                puck = game.gutter.pucks[i]
                valid_state = (puck.state == STATE_GUTTER or puck.state == STATE_READY)
                
                if valid_state and puck.owner == game.current_turn:
                    if puck.get_screen_pos().distance_to(m_pos) < puck.radius_px:
                        self.selected_puck = puck
                        self.selected_puck.state = STATE_SELECTED
                        self.selected_puck.is_selected = True
                        self.throw_history = []
                        # Move to top of list for rendering order
                        game.gutter.pucks.append(game.gutter.pucks.pop(i))
                        break

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.selected_puck:
                m_pos = pygame.mouse.get_pos()
                
                on_board = game.surface_rect.collidepoint(m_pos)
                behind_line = m_pos[0] < control_limit_screen_x
                
                if on_board and behind_line:
                    self.execute_throw(game)
                else:
                    self.cancel_throw(game)

        elif event.type == pygame.MOUSEMOTION:
            if self.selected_puck:
                m_pos = pygame.mouse.get_pos()
                g_left = constants.GUTTER_PADDING_LEFT
                g_y = constants.GUTTER_PADDING_Y
                ppi = constants.PPI

                x_in = (m_pos[0] - g_left) / ppi
                y_in = (m_pos[1] - g_y) / ppi
                self.selected_puck.set_pos(x_in, y_in)
                
                # Check constraints with other pucks (Gutter logic mainly)
                active_obstacles = [] 
                game.gutter.update_constraints(
                    self.selected_puck, 
                    game.screen_w, 
                    game.screen_h,
                    active_obstacles
                )

                self.throw_history.append(m_pos)
                if len(self.throw_history) > 3:
                    self.throw_history.pop(0)

    def update_hover(self, game):
        for puck in game.gutter.pucks:
            puck.highlighted = False

        if game.state != "GAME" or game.game_state != "AIMING":
            return

        m_pos = pygame.mouse.get_pos()
        for puck in game.gutter.pucks:
            valid_state = (puck.state == STATE_GUTTER or puck.state == STATE_READY)
            
            if valid_state and not self.selected_puck:
                if game.game_over or puck.owner == game.current_turn:
                    if puck.get_screen_pos().distance_to(m_pos) < puck.radius_px:
                        puck.highlighted = True

    def cancel_throw(self, game):
        self.selected_puck.is_selected = False
        touching = game.table.is_touching_table(self.selected_puck)
        if touching:
            self.selected_puck.state = STATE_READY
        else:
            self.selected_puck.state = STATE_GUTTER
            
        self.selected_puck = None
        self.throw_history = []

    def execute_throw(self, game):
        if len(self.throw_history) < 2 or not self.selected_puck: 
            self.cancel_throw(game)
            return

        start = self.throw_history[0]
        end = self.throw_history[-1]
        
        ppi = constants.PPI
        dampener = 3.0
        power_x = ((end[0] - start[0]) / ppi) / dampener
        power_y = ((end[1] - start[1]) / ppi) / dampener
        
        current_speed = math.hypot(power_x, power_y)
        
        if current_speed > 0.5:
            if current_speed > MAX_POWER:
                scale = MAX_POWER / current_speed
                power_x *= scale
                power_y *= scale

            game.shoot_puck(self.selected_puck, power_x, power_y)
        else:
            self.cancel_throw(game)