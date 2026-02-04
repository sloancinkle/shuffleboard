import pygame
import random
import math
from .. import constants
from .. import physics 
from ..constants import WOOD_LIGHT, BLACK, \
                        THROW_LINE_FT, FOUL_LINE_FT, REAL_BOARD_WIDTH, \
                        STATE_GUTTER, STATE_SELECTED, STATE_READY, \
                        STATE_THROWN, STATE_ON_BOARD, LINE_WIDTH, BLUE, RED

class Table:
    def __init__(self, screen_width, screen_height, surface_rect, board_length_ft):
        self.w = screen_width
        self.h = screen_height
        self.rect = surface_rect
        self.board_length_ft = board_length_ft
        
        scale = constants.PPI / 10.0
        self.font = pygame.font.SysFont("arial", int(32 * scale), bold=True)

    def is_touching_table(self, puck):
        board_len_in = self.rect.width / constants.PPI
        if (puck.x_in + puck.radius_in < 0) or \
           (puck.x_in - puck.radius_in > board_len_in) or \
           (puck.y_in + puck.radius_in < 0) or \
           (puck.y_in - puck.radius_in > REAL_BOARD_WIDTH):
            return False
        return True

    def is_puck_stable(self, puck):
        board_len_in = self.rect.width / constants.PPI
        tolerance = puck.radius_in * .22
        
        if puck.x_in < -tolerance or puck.x_in > board_len_in + tolerance:
            return False
        if puck.y_in < -tolerance or puck.y_in > REAL_BOARD_WIDTH + tolerance:
            return False
        return True

    def get_throw_line_inches(self):
        return THROW_LINE_FT * 12

    def draw(self, screen):
        pygame.draw.rect(screen, WOOD_LIGHT, self.rect)
        
        right = self.rect.right
        left = self.rect.left
        top = self.rect.top
        bottom = self.rect.bottom
        
        ppi = constants.PPI
        
        throw_line_x = left + (THROW_LINE_FT * 12 * ppi)
        foul_line_x = right - (FOUL_LINE_FT * 12 * ppi)
        
        line_3_x = right - (6 * ppi)   
        line_2_x = right - (12 * ppi)  

        if self.board_length_ft > 9:
            self.draw_dashed_line(screen, BLUE, (throw_line_x, top), (throw_line_x, bottom), width=LINE_WIDTH)

        pygame.draw.line(screen, RED, (foul_line_x, top), (foul_line_x, bottom), LINE_WIDTH)
        pygame.draw.line(screen, BLACK, (line_3_x, top), (line_3_x, bottom), LINE_WIDTH)
        pygame.draw.line(screen, BLACK, (line_2_x, top), (line_2_x, bottom), LINE_WIDTH)

        # Labels
        self.draw_text(screen, "3", (right + line_3_x) / 2, self.rect.centery)
        self.draw_text(screen, "2", (line_3_x + line_2_x) / 2, self.rect.centery)
        label_1_x = line_2_x - (3 * ppi)
        self.draw_text(screen, "1", label_1_x, self.rect.centery)

    def draw_dashed_line(self, screen, color, start, end, width=1, dash_len=10):
        x1, y1 = start
        x2, y2 = end
        total_len = y2 - y1
        dashes = int(total_len / dash_len)
        for i in range(dashes):
            if i % 2 == 0:
                s_y = y1 + (i * dash_len)
                e_y = y1 + ((i + 1) * dash_len)
                pygame.draw.line(screen, color, (x1, s_y), (x1, e_y), width)

    def draw_text(self, screen, text, x, y):
        surf = self.font.render(text, True, (180, 140, 100)) 
        rect = surf.get_rect(center=(x, y))
        screen.blit(surf, rect)

class Gutter:
    def __init__(self, puck_size):
        self.pucks = [] 
        self.puck_size = puck_size
        self.free_play = False

    def add_puck(self, puck):
        if puck not in self.pucks:
            self.pucks.append(puck)

    def scatter_pucks(self, screen_h):
        placed_positions = []
        for puck in self.pucks:
            self._place_puck_safe(puck, screen_h, placed_positions)
            px = int(constants.GUTTER_PADDING_LEFT + (puck.x_in * constants.PPI))
            py = int(constants.GUTTER_PADDING_Y + (puck.y_in * constants.PPI))
            placed_positions.append(pygame.math.Vector2(px, py))

    def place_puck_nearest(self, puck, screen_h, screen_w):
        target_x = puck.x_in
        target_y = puck.y_in
        existing_positions = []
        for p in self.pucks:
            if p != puck and p.state == STATE_GUTTER:
                existing_positions.append(pygame.math.Vector2(p.x_in, p.y_in))
        
        g_left = constants.GUTTER_PADDING_LEFT
        g_y = constants.GUTTER_PADDING_Y
        ppi = constants.PPI

        min_x = -g_left / ppi
        max_x = (screen_w - g_left) / ppi
        min_y = -g_y / ppi
        max_y = (screen_h - g_y) / ppi
        
        radius_step = 0.5 
        found = False
        search_radius = 0
        final_x, final_y = target_x, target_y
        attempts = 0
        while not found and attempts < 100:
            if search_radius == 0:
                points = [(target_x, target_y)]
            else:
                points = []
                circ = 2 * math.pi * search_radius
                steps = max(8, int(circ / radius_step)) 
                for i in range(steps):
                    a = (i / steps) * 2 * math.pi
                    px = target_x + math.cos(a) * search_radius
                    py = target_y + math.sin(a) * search_radius
                    points.append((px, py))
            
            for (px, py) in points:
                if px < min_x + puck.radius_in or px > max_x - puck.radius_in: continue
                if py < min_y + puck.radius_in or py > max_y - puck.radius_in: continue
                
                on_wood = (px + puck.radius_in > 0) and \
                          (py + puck.radius_in > 0 and py - puck.radius_in < REAL_BOARD_WIDTH)
                
                if on_wood: continue
                overlap = False
                for ex in existing_positions:
                    dist = math.hypot(px - ex.x, py - ex.y)
                    if dist < (puck.radius_in * 2 + 0.1): 
                        overlap = True; break
                if not overlap:
                    final_x, final_y = px, py
                    found = True
                    break
            search_radius += radius_step
            attempts += 1
        puck.set_pos(final_x, final_y)

    def _place_puck_safe(self, puck, screen_h, existing_positions):
        g_left = constants.GUTTER_PADDING_LEFT
        g_y = constants.GUTTER_PADDING_Y
        ppi = constants.PPI

        min_x = 10 
        max_x = g_left - puck.radius_px - 4
        min_y = g_y
        max_y = screen_h - g_y
        r_px = puck.radius_px
        min_dist = r_px * 2 + 2

        attempts = 0
        placed = False
        
        while attempts < 200:
            rx = random.randint(min_x, max_x)
            ry = random.randint(min_y, max_y)
            pos = pygame.math.Vector2(rx, ry)
            overlap = False
            for existing_pos in existing_positions:
                if pos.distance_to(existing_pos) < min_dist:
                    overlap = True; break
            if not overlap:
                x_in = (rx - g_left) / ppi
                y_in = (ry - g_y) / ppi
                puck.set_pos(x_in, y_in)
                placed = True
                return
            attempts += 1
            
        if not placed:
            fallback_x = 25 
            fallback_y = g_y + 30 + (len(existing_positions) * (r_px*2 + 5))
            if fallback_y > screen_h - 50: fallback_y = g_y + 30
            x_in = (fallback_x - g_left) / ppi
            y_in = (fallback_y - g_y) / ppi
            puck.set_pos(x_in, y_in)

    def update_constraints(self, selected_puck, screen_w, screen_h, active_pucks_obstacles):
        g_left = constants.GUTTER_PADDING_LEFT
        g_right = constants.GUTTER_PADDING_RIGHT
        g_y = constants.GUTTER_PADDING_Y
        ppi = constants.PPI

        board_len_in = (screen_w - g_left - g_right) / ppi
        throw_line_in = THROW_LINE_FT * 12

        min_screen_x = -g_left / ppi
        max_screen_x = (screen_w - g_left) / ppi 
        min_screen_y = -g_y / ppi
        max_screen_y = (screen_h - g_y) / ppi

        hand_pucks = [p for p in self.pucks if p.state in (STATE_GUTTER, STATE_SELECTED)]

        for _ in range(3): 
            for i in range(len(hand_pucks)):
                p1 = hand_pucks[i]
                for j in range(i + 1, len(hand_pucks)):
                    p2 = hand_pucks[j]
                    
                    # UPDATED: Use dynamic collision check between hand pucks (Gutter vs Selected)
                    # This allows dragging a puck to "kick" other gutter pucks around
                    if p1 == selected_puck:
                        physics.check_puck_collision(p1, p2)
                    elif p2 == selected_puck:
                        physics.check_puck_collision(p2, p1)
                    else:
                        physics.resolve_static_overlap(p1, p2)

        for hand_p in hand_pucks:
            for active_p in active_pucks_obstacles:
                if active_p.state == STATE_ON_BOARD:
                    if self.free_play:
                        if hand_p.state == STATE_SELECTED:
                            physics.check_puck_collision(hand_p, active_p)
                        else:
                            pass
                    else:
                        pass
                else:
                    if hand_p.state == STATE_SELECTED:
                        physics.check_puck_collision(hand_p, active_p)
                    else:
                        physics.resolve_static_push(active_p, hand_p)

        for puck in hand_pucks:
            if puck.x_in < min_screen_x + puck.radius_in: puck.x_in = min_screen_x + puck.radius_in
            if puck.x_in > max_screen_x - puck.radius_in: puck.x_in = max_screen_x - puck.radius_in
            if puck.y_in < min_screen_y + puck.radius_in: puck.y_in = min_screen_y + puck.radius_in
            if puck.y_in > max_screen_y - puck.radius_in: puck.y_in = max_screen_y - puck.radius_in

            check_obstacle = True
            
            if self.free_play:
                if puck.state == STATE_SELECTED:
                    check_obstacle = False
                else:
                    check_obstacle = True
            
            if check_obstacle:
                if puck.state == STATE_GUTTER:
                    obs_min_x = 0
                else: 
                    obs_min_x = throw_line_in
                
                obs_max_x = board_len_in
                obs_min_y = 0
                obs_max_y = REAL_BOARD_WIDTH

                self.resolve_rect_obstacle(puck, obs_min_x, obs_max_x, obs_min_y, obs_max_y)

    def resolve_solid_collision(self, mobile_puck, static_puck):
        physics.resolve_static_push(static_puck, mobile_puck)

    def resolve_rect_obstacle(self, puck, r_min_x, r_max_x, r_min_y, r_max_y):
        cx = max(r_min_x, min(puck.x_in, r_max_x))
        cy = max(r_min_y, min(puck.y_in, r_max_y))

        dx = puck.x_in - cx
        dy = puck.y_in - cy
        dist_sq = dx*dx + dy*dy
        
        if dist_sq < (puck.radius_in * puck.radius_in):
            nx, ny = 0, 0
            if dist_sq == 0:
                d_left = abs(puck.x_in - r_min_x)
                d_right = abs(puck.x_in - r_max_x)
                d_top = abs(puck.y_in - r_min_y)
                d_bottom = abs(puck.y_in - r_max_y)
                m = min(d_left, d_right, d_top, d_bottom)
                if m == d_left: 
                    puck.x_in = r_min_x - puck.radius_in
                    nx, ny = -1, 0
                elif m == d_right: 
                    puck.x_in = r_max_x + puck.radius_in
                    nx, ny = 1, 0
                elif m == d_top: 
                    puck.y_in = r_min_y - puck.radius_in
                    nx, ny = 0, -1
                elif m == d_bottom: 
                    puck.y_in = r_max_y + puck.radius_in
                    nx, ny = 0, 1
            else:
                dist = math.sqrt(dist_sq)
                overlap = puck.radius_in - dist
                nx = dx / dist
                ny = dy / dist
                puck.x_in += nx * overlap
                puck.y_in += ny * overlap

            restitution = 0.7
            vn = (puck.dx * nx) + (puck.dy * ny)
            if vn < 0:
                j = -(1 + restitution) * vn
                puck.dx += j * nx
                puck.dy += j * ny

    def draw_gutter_layer(self, screen):
        for puck in self.pucks:
            if puck.state == STATE_GUTTER:
                puck.draw(screen)

    def draw_active_layer(self, screen):
        for puck in self.pucks:
            if puck.state in [STATE_SELECTED, STATE_READY, STATE_THROWN]:
                puck.draw(screen)

    def draw_puck_shadows(self, screen, surface_rect, target_states):
        shadow_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        offset = 2 
        
        for puck in self.pucks:
            if puck.state in target_states:
                pos = puck.get_screen_pos()
                pygame.draw.circle(shadow_surf, (0, 0, 0, 60), 
                                   (int(pos.x + offset), int(pos.y + offset)), 
                                   puck.radius_px)
        
        shadow_surf.fill((0, 0, 0, 0), surface_rect)
        screen.blit(shadow_surf, (0, 0))

    def draw_edging_layer(self, screen):
        for puck in self.pucks:
            if puck.state == STATE_ON_BOARD:
                puck.draw(screen)