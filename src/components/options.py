import pygame
import random
import math
from .. import constants
from .. import physics
from ..components.puck import Puck
from ..constants import WHITE, BLACK, WOOD_DARK, WOOD_LIGHT, \
                        PUCK_MEDIUM, PUCK_LARGE, PUCK_COLORS, \
                        PPI, TABLE_FRICTION, P1, P2, \
                        STATE_READY, STATE_SELECTED, MAX_POWER

class Options:
    def __init__(self, current_length, current_puck_size):
        self.length = current_length
        self.puck_size = current_puck_size
        self.ppi = constants.PPI 
        self.edging_enabled = True 
        self.target_score = 21
        
        self.p1_color = "Red"
        self.p2_color = "Blue"
        self.available_colors = list(PUCK_COLORS.keys())
        
        self.orig_length = current_length
        self.orig_puck_size = current_puck_size
        self.orig_edging = True
        self.orig_target = 21
        
        # Track integer length to trigger resizes only on foot changes
        self.last_int_length = int(current_length)

        self.min_len = 9
        self.max_len = 22
        
        self.update_fonts()
        
        # Rects
        self.slider_rect = pygame.Rect(0,0,0,0)
        self.ppi_up_rect = pygame.Rect(0,0,0,0)
        self.ppi_down_rect = pygame.Rect(0,0,0,0)
        
        self.btn_size_rect = pygame.Rect(0,0,0,0)
        self.btn_score_rect = pygame.Rect(0,0,0,0)
        self.btn_edge_rect = pygame.Rect(0,0,0,0)
        self.start_btn_rect = pygame.Rect(0,0,0,0)
        self.p1_area_rect = pygame.Rect(0,0,0,0)
        self.p2_area_rect = pygame.Rect(0,0,0,0)
        
        # Interaction / Physics for Menu
        self.menu_pucks_p1 = []
        self.menu_pucks_p2 = []
        self.menu_pucks = []
        
        self.handle_radius = 12
        self.dragging_slider = False
        self.selected_puck = None 
        self.throw_history = []
        
        self.refresh_puck_positions()

    def update_fonts(self):
        scale = self.ppi / 10.0
        self.small_label_font = pygame.font.SysFont("arial", int(18 * scale), bold=True)
        self.btn_font = pygame.font.SysFont("arial", int(14 * scale), bold=True)
        self.font = pygame.font.SysFont("arial", int(20 * scale), bold=True)

    def set_initials(self, length, puck_size, target_score):
        self.orig_length = length
        self.orig_puck_size = puck_size
        self.orig_edging = self.edging_enabled
        self.orig_target = target_score
        self.last_int_length = int(length)
        
    def refresh_puck_positions(self):
        self.menu_pucks_p1 = []
        self.menu_pucks_p2 = []
        self.menu_pucks = []
        
        self.menu_pucks_p1 = self._create_puck_set(P1, exclude_color=self.p2_color)
        self.menu_pucks_p2 = self._create_puck_set(P2, exclude_color=self.p1_color)
        
        self.menu_pucks = self.menu_pucks_p1 + self.menu_pucks_p2

    def _create_puck_set(self, player_id, exclude_color):
        pucks = []
        for color_name in self.available_colors:
            if color_name == exclude_color:
                continue
            
            p = Puck(player_id, self.puck_size, PUCK_COLORS[color_name])
            p.color_name = color_name 
            p.menu_group = player_id
            
            p.x_in = random.uniform(1, 10)
            p.y_in = random.uniform(1, 5)
            pucks.append(p)
        return pucks

    def update_layout(self, screen_w, screen_h):
        self.ppi = constants.PPI  # Sync with current global PPI
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.update_fonts() # Ensure fonts scale with new PPI
        
        col_gap = int(2.0 * self.ppi)
        margin = int(6.0 * self.ppi) 
        
        left_w = int(36.0 * self.ppi) 
        right_w = int(15.0 * self.ppi)
        
        used_width = left_w + right_w + (col_gap * 2) + (margin * 2)
        center_w = max(int(10 * self.ppi), screen_w - used_width)
        
        start_x = (screen_w - (left_w + col_gap + center_w + col_gap + right_w)) // 2
        left_x = start_x
        center_x = left_x + left_w + col_gap
        right_x = center_x + center_w + col_gap
        
        # --- LEFT COLUMN LAYOUT ---
        slider_row_h = int(3.5 * self.ppi)
        btn_h = int(6.0 * self.ppi)   
        gap_between_rows = int(3.5 * self.ppi) 
        
        total_left_h = slider_row_h + gap_between_rows + btn_h
        left_start_y = (screen_h - total_left_h) // 2
        
        # Slider now extends the full width of the left column
        self.slider_rect = pygame.Rect(left_x, left_start_y, left_w, slider_row_h)
        
        # Toggles
        row2_y = left_start_y + slider_row_h + gap_between_rows
        btn_gap = int(0.5 * self.ppi)
        btn_w = (left_w - (2 * btn_gap)) // 3
        
        self.btn_size_rect = pygame.Rect(left_x, row2_y, btn_w, btn_h)
        self.btn_score_rect = pygame.Rect(self.btn_size_rect.right + btn_gap, row2_y, btn_w, btn_h)
        self.btn_edge_rect = pygame.Rect(self.btn_score_rect.right + btn_gap, row2_y, btn_w, btn_h)

        # --- CENTER COLUMN (Zones) ---
        total_h = int(18.0 * self.ppi) 
        box_gap = int(1.0 * self.ppi)
        box_h = (total_h - box_gap) // 2
        colors_top_y = (screen_h - total_h) // 2
        
        self.p1_area_rect = pygame.Rect(center_x, colors_top_y, center_w, box_h)
        self.p2_area_rect = pygame.Rect(center_x, self.p1_area_rect.bottom + box_gap, center_w, box_h)
        
        # --- RIGHT COLUMN ---
        self.start_btn_rect = pygame.Rect(right_x, (screen_h - btn_h) // 2, right_w, btn_h)

        # Force all menu pucks to update their pixel radius and stay in bounds
        for p in self.menu_pucks:
            p.update_visuals(self.puck_size, constants.PUCK_COLORS[p.color_name])
            
        self._confine_pucks(self.menu_pucks_p1, self.p1_area_rect)
        self._confine_pucks(self.menu_pucks_p2, self.p2_area_rect)

    def _confine_pucks(self, pucks, rect):
        if rect.width == 0: return
        g_left = constants.GUTTER_PADDING_LEFT
        g_y = constants.GUTTER_PADDING_Y
        ppi = constants.PPI

        min_x = (rect.x - g_left) / ppi
        max_x = (rect.right - g_left) / ppi
        min_y = (rect.y - g_y) / ppi
        max_y = (rect.bottom - g_y) / ppi

        for p in pucks:
            if not (min_x + p.radius_in <= p.x_in <= max_x - p.radius_in) or \
               not (min_y + p.radius_in <= p.y_in <= max_y - p.radius_in):
                
                rx = random.uniform(min_x + p.radius_in, max_x - p.radius_in)
                ry = random.uniform(min_y + p.radius_in, max_y - p.radius_in)
                p.set_pos(rx, ry)
                p.dx = 0; p.dy = 0

    def handle_event(self, event):
        m_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_btn_rect.collidepoint(m_pos): return "START"
            
            if self.btn_size_rect.collidepoint(m_pos): self.puck_size = PUCK_LARGE if self.puck_size == PUCK_MEDIUM else PUCK_MEDIUM
            if self.btn_score_rect.collidepoint(m_pos): self.target_score = 15 if self.target_score == 21 else 21
            if self.btn_edge_rect.collidepoint(m_pos): self.edging_enabled = not self.edging_enabled

            if math.hypot(m_pos[0]-self.get_handle_x(), m_pos[1]-self.slider_rect.centery) < self.handle_radius:
                self.dragging_slider = True

            clicked_puck = self._get_puck_at(m_pos)
            if clicked_puck:
                new_color = clicked_puck.color_name
                owner_group = clicked_puck.menu_group
                
                if owner_group == P1:
                    old_p1_color = self.p1_color
                    if new_color != old_p1_color:
                        self.p1_color = new_color
                        self._swap_puck_option(self.menu_pucks_p2, new_color, old_p1_color)
                        
                elif owner_group == P2:
                    old_p2_color = self.p2_color
                    if new_color != old_p2_color:
                        self.p2_color = new_color
                        self._swap_puck_option(self.menu_pucks_p1, new_color, old_p2_color)

                self.selected_puck = clicked_puck
                self.selected_puck.state = STATE_SELECTED
                self.selected_puck.is_moving = False
                self.selected_puck.dx = 0; self.selected_puck.dy = 0
                self.throw_history = [m_pos]

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_slider = False
            if self.selected_puck:
                self._execute_throw()
                self.selected_puck.state = STATE_READY 
                self.selected_puck = None
                self.throw_history = []
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_slider:
                m_x = max(self.slider_rect.left, min(m_pos[0], self.slider_rect.right))
                ratio = (m_x - self.slider_rect.left) / self.slider_rect.width
                self.length = self.min_len + (ratio * (self.max_len - self.min_len))
                
                new_int_len = int(self.length)
                
                if self.last_int_length < 15 and new_int_len >= 15:
                    self.puck_size = PUCK_LARGE
                
                elif self.last_int_length >= 15 and new_int_len < 15:
                    self.puck_size = PUCK_MEDIUM

                if new_int_len != self.last_int_length:
                    self.last_int_length = new_int_len
                    return "SLIDER_UPDATE"
            
            if self.selected_puck:
                limit_rect = self.p1_area_rect if self.selected_puck.menu_group == P1 else self.p2_area_rect
                g_left = constants.GUTTER_PADDING_LEFT
                g_y = constants.GUTTER_PADDING_Y
                ppi = self.ppi
                
                target_x_in = (m_pos[0] - g_left) / ppi
                target_y_in = (m_pos[1] - g_y) / ppi
                
                min_x = (limit_rect.x - g_left) / ppi
                max_x = (limit_rect.right - g_left) / ppi
                min_y = (limit_rect.y - g_y) / ppi
                max_y = (limit_rect.bottom - g_y) / ppi
                
                r = self.selected_puck.radius_in
                
                clamped_x = max(min_x + r, min(target_x_in, max_x - r))
                clamped_y = max(min_y + r, min(target_y_in, max_y - r))
                
                self.selected_puck.set_pos(clamped_x, clamped_y)
                
                clamped_px = (clamped_x * ppi) + g_left
                clamped_py = (clamped_y * ppi) + g_y
                
                self.throw_history.append((clamped_px, clamped_py))
                if len(self.throw_history) > 3:
                    self.throw_history.pop(0)

        return None

    def _swap_puck_option(self, puck_list, target_color_to_remove, new_color_to_add):
        for p in puck_list:
            if p.color_name == target_color_to_remove:
                p.color_name = new_color_to_add
                return

    def _get_puck_at(self, m_pos):
        for p in self.menu_pucks:
            p_pos = p.get_screen_pos()
            if p_pos.distance_to(m_pos) < p.radius_px:
                return p
        return None

    def _execute_throw(self):
        if len(self.throw_history) < 2: return
        start = self.throw_history[0]
        end = self.throw_history[-1]
        dampener = 3.0
        ppi = self.ppi
        power_x = ((end[0] - start[0]) / ppi) / dampener
        power_y = ((end[1] - start[1]) / ppi) / dampener
        current_speed = math.hypot(power_x, power_y)
        if current_speed > MAX_POWER:
            scale = MAX_POWER / current_speed
            power_x *= scale
            power_y *= scale
        self.selected_puck.dx = power_x
        self.selected_puck.dy = power_y
        self.selected_puck.is_moving = True

    def update_physics(self):
        g_left = constants.GUTTER_PADDING_LEFT
        g_y = constants.GUTTER_PADDING_Y
        ppi = self.ppi

        def get_constraints(rect):
            return (
                (rect.x - g_left) / ppi,
                (rect.right - g_left) / ppi,
                (rect.y - g_y) / ppi,
                (rect.bottom - g_y) / ppi
            )

        p1_cons = get_constraints(self.p1_area_rect)
        p2_cons = get_constraints(self.p2_area_rect)

        for p in self.menu_pucks:
            if p == self.selected_puck: continue
            physics.update_puck_movement(p, TABLE_FRICTION)
            constraints = p1_cons if p.menu_group == P1 else p2_cons
            physics.resolve_rect_container(p, *constraints)
        
        for i in range(len(self.menu_pucks)):
            p1 = self.menu_pucks[i]
            for j in range(i + 1, len(self.menu_pucks)):
                p2 = self.menu_pucks[j]
                if p1.menu_group == p2.menu_group:
                    physics.check_puck_collision(p1, p2)

    def get_handle_x(self):
        ratio = (self.length - self.min_len) / (self.max_len - self.min_len)
        return self.slider_rect.left + (self.slider_rect.width * ratio)
    
    def _draw_btn(self, screen, rect, text):
        pygame.draw.rect(screen, WOOD_LIGHT, rect, border_radius=8)
        lbl = self.btn_font.render(text, True, BLACK)
        screen.blit(lbl, lbl.get_rect(center=rect.center))

    def _draw_arrow(self, screen, rect, direction):
        pygame.draw.rect(screen, WOOD_LIGHT, rect, border_radius=4)
        cx, cy = rect.centerx, rect.centery
        arrow_size = int(0.5 * self.ppi) 
        if direction == "up":
            points = [(cx, cy - arrow_size), (cx - arrow_size, cy + arrow_size), (cx + arrow_size, cy + arrow_size)]
        else:
            points = [(cx, cy + arrow_size), (cx - arrow_size, cy - arrow_size), (cx + arrow_size, cy - arrow_size)]
        pygame.draw.polygon(screen, BLACK, points)
        
    def draw(self, screen):
        self.update_physics()
        screen.fill(constants.WOOD_DARK)
        
        # --- Labels ---
        lbl_y = self.slider_rect.top - int(1.5 * self.ppi)
        
        # Only draw the Table Length label
        len_lbl = self.small_label_font.render(f"Table Length: {int(self.length)} Ft", True, constants.WHITE)
        screen.blit(len_lbl, len_lbl.get_rect(center=(self.slider_rect.centerx, lbl_y)))
        
        # --- Slider ---
        track_rect = pygame.Rect(self.slider_rect.left, self.slider_rect.centery - 4, self.slider_rect.width, 8)
        pygame.draw.rect(screen, (100, 50, 0), track_rect, border_radius=4)
        pygame.draw.circle(screen, constants.WOOD_LIGHT, (int(self.get_handle_x()), int(self.slider_rect.centery)), self.handle_radius)

        self._draw_btn(screen, self.btn_size_rect, "Medium Pucks" if self.puck_size == PUCK_MEDIUM else "Large Pucks")
        self._draw_btn(screen, self.btn_score_rect, f"Game to {self.target_score}")
        self._draw_btn(screen, self.btn_edge_rect, "+1 for Edge" if self.edging_enabled else "+0 for Edge")

        # --- Zones ---
        self._draw_zone_no_outline(screen, self.p1_area_rect)
        self._draw_zone_no_outline(screen, self.p2_area_rect)

        # --- Resume ---
        has_changed = (int(self.length) != int(self.orig_length)) or \
                      (self.puck_size != self.orig_puck_size) or \
                      (self.edging_enabled != self.orig_edging) or \
                      (self.target_score != self.orig_target)
        self._draw_btn(screen, self.start_btn_rect, "RESET" if has_changed else "RESUME")

        # --- Pucks ---
        m_pos = pygame.mouse.get_pos()
        for p in self.menu_pucks:
            target_color = self.p1_color if p.menu_group == P1 else self.p2_color
            is_active_color = (p.color_name == target_color)
            
            p_pos = p.get_screen_pos()
            is_hovered = p_pos.distance_to(m_pos) < p.radius_px
            p.highlighted = (is_active_color or is_hovered)
            
            p.update_visuals(self.puck_size, PUCK_COLORS[p.color_name])
            p.draw(screen)

    def _draw_zone_no_outline(self, screen, rect):
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 60)) 
        screen.blit(shadow_surf, (rect.x + 4, rect.y + 4))
        pygame.draw.rect(screen, WOOD_LIGHT, rect)