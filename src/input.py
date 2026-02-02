import pygame
import math
from . import constants
from .constants import THROW_LINE_FT, MAX_POWER, \
                       STATE_GUTTER, STATE_SELECTED, STATE_READY, \
                       STATE_ON_BOARD, STATE_THROWN

class InputHandler:
    def __init__(self):
        self.selected_puck = None
        self.throw_history = []
    
    def reset(self):
        self.selected_puck = None
        self.throw_history = []

    def handle_input(self, event, game):
        # In Free Play, allow input regardless of game state
        if not game.game_over and game.game_state != "AIMING":
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
                
                if game.game_over:
                    valid_state = True
                else:
                    valid_state = (puck.state == STATE_GUTTER or puck.state == STATE_READY)
                
                if not game.game_over and puck.is_moving:
                    valid_state = False

                if valid_state:
                    is_owner = (puck.owner == game.current_turn)
                    if game.game_over or is_owner:
                        if puck.get_screen_pos().distance_to(m_pos) < puck.radius_px:
                            self.selected_puck = puck
                            self.selected_puck.state = STATE_SELECTED
                            self.selected_puck.is_selected = True
                            
                            self.selected_puck.dx = 0
                            self.selected_puck.dy = 0
                            self.selected_puck.is_moving = False
                            
                            self.throw_history = []
                            game.gutter.pucks.append(game.gutter.pucks.pop(i))
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.selected_puck:
                m_pos = pygame.mouse.get_pos()
                on_board = game.surface_rect.collidepoint(m_pos)
                
                # Determine if release is valid
                valid_release = False
                
                if game.game_over:
                    valid_release = True
                else:
                    if not on_board:
                        # Gutter throw is valid but won't score/count
                        valid_release = True
                    else:
                        # Board throw must be behind line
                        if m_pos[0] < control_limit_screen_x:
                            valid_release = True
                        else:
                            valid_release = False
                
                if valid_release:
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
                
                active_obstacles = [
                    p for p in game.gutter.pucks 
                    if p is not self.selected_puck 
                    and p.state in (STATE_ON_BOARD, STATE_THROWN, STATE_READY)
                ]

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

        if not game.game_over:
            if game.state != "GAME" or game.game_state != "AIMING":
                return

        m_pos = pygame.mouse.get_pos()
        for puck in game.gutter.pucks:
            if game.game_over:
                valid_state = True
            else:
                valid_state = (puck.state == STATE_GUTTER or puck.state == STATE_READY)
            
            if valid_state and not self.selected_puck:
                if game.game_over or puck.owner == game.current_turn:
                    if puck.get_screen_pos().distance_to(m_pos) < puck.radius_px:
                        puck.highlighted = True

    def cancel_throw(self, game):
        self.selected_puck.is_selected = False
        touching = game.table.is_touching_table(self.selected_puck)
        if touching:
            if game.game_over:
                self.selected_puck.state = STATE_ON_BOARD
            else:
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

            # Check where the puck is actually released
            m_pos = pygame.mouse.get_pos()
            on_board = game.surface_rect.collidepoint(m_pos)
            
            # Count throw only if on board and not free play
            count_throw = False
            if not game.game_over and on_board:
                count_throw = True

            game.shoot_puck(self.selected_puck, power_x, power_y, count_throw)
        else:
            self.cancel_throw(game)