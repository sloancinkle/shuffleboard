import pygame
import math
from .. import constants
from ..constants import MIN_SPEED, LINE_WIDTH, \
                        STATE_GUTTER, STATE_THROWN, STATE_ON_BOARD, STATE_READY, STATE_SELECTED, \
                        P1, BLACK

class Puck:
    def __init__(self, owner, diameter, color_rgb, font="couriernew", text_color=BLACK):
        self.owner = owner 
        self.update_visuals(diameter, color_rgb)
        
        # Visual settings (stored for memory saving)
        self.font_name = font
        self.text_color = text_color
        
        # Physics State
        self.x_in = 0
        self.y_in = 0
        self.dx = 0
        self.dy = 0
        self.is_moving = False
        self.state = STATE_GUTTER 
        
        # Interaction State
        self.highlighted = False 
        self.is_selected = False

    def update_visuals(self, diameter, color_rgb):
        self.radius_in = diameter / 2.0
        self.radius_px = int(self.radius_in * constants.PPI)
        self.color = color_rgb

    def set_pos(self, x_in, y_in):
        self.x_in = x_in
        self.y_in = y_in

    def get_screen_pos(self):
        px = int(constants.GUTTER_PADDING_LEFT + (self.x_in * constants.PPI))
        py = int(constants.GUTTER_PADDING_Y + (self.y_in * constants.PPI))
        return pygame.math.Vector2(px, py)

    def update(self, friction, bounds_in):
        # Basic movement update called by game loop
        if self.is_moving:
            self.x_in += self.dx
            self.y_in += self.dy
            self.dx *= friction
            self.dy *= friction
            speed = math.hypot(self.dx, self.dy)
            if speed < MIN_SPEED:
                self.dx = 0
                self.dy = 0
                self.is_moving = False

    def draw(self, screen):
        pos = self.get_screen_pos()
        ppi = constants.PPI
        
        # Highlight Logic
        valid_highlight_state = (self.state == STATE_GUTTER or self.state == STATE_READY)
        if self.highlighted and valid_highlight_state:
            pygame.draw.circle(screen, (255, 255, 255), (int(pos.x), int(pos.y)), self.radius_px + 3)

        # Draw Puck Body
        draw_color = self.color
        # Conflict Check: If Text Color == Body Color, make Body Dark Grey
        if self.color == self.text_color:
            draw_color = (50, 50, 50)

        pygame.draw.circle(screen, draw_color, (int(pos.x), int(pos.y)), self.radius_px)
        pygame.draw.circle(screen, BLACK, (int(pos.x), int(pos.y)), self.radius_px, LINE_WIDTH)

        # Draw Text
        font_size = int(1.1 * ppi)
        try:
            puck_font = pygame.font.SysFont(self.font_name, font_size, bold=True)
        except:
            puck_font = pygame.font.SysFont("couriernew", font_size, bold=True)
        
        display_num = "" if self.owner == P1 else ""
        
        if display_num:
            text_surf = puck_font.render(display_num, True, self.text_color)
            text_rect = text_surf.get_rect(center=(int(pos.x), int(pos.y)))
            screen.blit(text_surf, text_rect)