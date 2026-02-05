import pygame
import random
import math
from .. import constants
from .. import physics
from ..components.puck import Puck
from ..constants import WHITE, BLACK, WOOD_DARK, WOOD_LIGHT, \
                        PUCK_COLORS, TABLE_FRICTION, P1, P2, \
                        STATE_READY, STATE_SELECTED, MAX_POWER

class Options:
    def __init__(self, current_length, current_puck_size):
        self.length = current_length
        self.puck_size = current_puck_size
        self.edging_enabled = True 
        self.target_score = 21
        
        self.p1_color = "Red"
        self.p2_color = "Blue"
        self.available_colors = list(PUCK_COLORS.keys())
        
        self.orig_length = current_length
        self.orig_puck_size = current_puck_size
        self.orig_edging = True
        self.orig_target = 21
        self.last_length = int(current_length)

        self.min_len = 9
        self.max_len = 22
        
        surface = pygame.display.get_surface()
        self.screen_w, self.screen_h = surface.get_size() if surface else (1000, 600)

        self.update_fonts()
        
        # Initialize all rects to empty
        self.slider_rect = pygame.Rect(0,0,0,0)
        self.btn_size_rect = pygame.Rect(0,0,0,0)
        self.btn_score_rect = pygame.Rect(0,0,0,0)
        self.btn_edge_rect = pygame.Rect(0,0,0,0)
        self.start_btn_rect = pygame.Rect(0,0,0,0)
        self.p1_area_rect = pygame.Rect(0,0,0,0)
        self.p2_area_rect = pygame.Rect(0,0,0,0)
        
        self.menu_pucks_p1 = []
        self.menu_pucks_p2 = []
        self.menu_pucks = []
        
        self.handle_radius = 12
        self.dragging_slider = False
        self.selected_puck = None 
        self.throw_history = []

        # Calculate initial layout but don't spawn pucks yet
        self.update_layout(self.screen_w, self.screen_h)

    def set_initials(self, length, puck_size, target_score):
        # 1. Update the actual active values
        self.length = length
        self.puck_size = puck_size
        self.target_score = target_score
        
        # 2. Update the 'original' values
        self.orig_length = length
        self.orig_puck_size = puck_size
        self.orig_edging = self.edging_enabled
        self.orig_target = target_score
        
        # 3. Update internal trackers
        self.last_length = int(length)
        self.last_int_length = int(length)
        
        self.update_layout(self.screen_w, self.screen_h)
        self.refresh_puck_positions()
        
    def refresh_puck_positions(self):
        self.menu_pucks_p1 = self._create_puck_set(P1, exclude_color=self.p2_color)
        self.menu_pucks_p2 = self._create_puck_set(P2, exclude_color=self.p1_color)
        self.menu_pucks = self.menu_pucks_p1 + self.menu_pucks_p2
        
        def scatter(pucks, rect):
            # Guard against zero-sized rects
            if rect.width <= 10: return
            
            g_left = constants.GUTTER_PADDING_LEFT
            g_y = constants.GUTTER_PADDING_Y
            ppi = constants.PPI
            
            # Convert screen rect to physics inches
            min_x = (rect.left - g_left) / ppi
            max_x = (rect.right - g_left) / ppi
            min_y = (rect.top - g_y) / ppi
            max_y = (rect.bottom - g_y) / ppi
            
            for p in pucks:
                # Add a small buffer so they don't spawn touching the wall
                p.x_in = random.uniform(min_x + p.radius_in + 0.1, max_x - p.radius_in - 0.1)
                p.y_in = random.uniform(min_y + p.radius_in + 0.1, max_y - p.radius_in - 0.1)
                p.dx = 0
                p.dy = 0

        scatter(self.menu_pucks_p1, self.p1_area_rect)
        scatter(self.menu_pucks_p2, self.p2_area_rect)
        
        # Immediate physics pass to push overlapping pucks apart
        for _ in range(50):
            self._confine_pucks(self.menu_pucks_p1, self.p1_area_rect)
            self._confine_pucks(self.menu_pucks_p2, self.p2_area_rect)

    def _create_puck_set(self, player_id, exclude_color):
        pucks = []
        for color_name in self.available_colors:
            if color_name == exclude_color: continue
            p = Puck(player_id, self.puck_size, PUCK_COLORS[color_name])
            p.color_name = color_name 
            p.menu_group = player_id
            p.x_in = random.uniform(1, 10)
            p.y_in = random.uniform(1, 5)
            pucks.append(p)
        return pucks

    def update_layout(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        
        # --- DEFINED HORIZONTAL SPECS (INCHES) ---
        # x calculation: Table Length (inches) - 108 inches
        current_tl_in = int(self.length) * 12
        x_in = current_tl_in - 108
        
        # Margins & Column Widths
        margin_left_in = (self.screen_w / constants.PPI - x_in - 116) / 2
        col_opt_in     = 34
        gap1_in        = 4
        col_table_in   = 62 + x_in
        gap2_in        = 4
        col_res_in     = 12
        # margin_right_in = 16 (implied by window width, used for validation)

        # Convert to Pixels
        ppi = constants.PPI
        
        # Horizontal Positions (strictly additive)
        pos_left_margin = int(margin_left_in * ppi)
        
        # 1. Options Column (Starts after left margin)
        opt_x = pos_left_margin
        opt_w = int(col_opt_in * ppi)
        
        # 2. Table Column (Starts after Options + Gap1)
        table_x = opt_x + opt_w + int(gap1_in * ppi)
        table_w = int(col_table_in * ppi)
        
        # 3. Resume Column (Starts after Table + Gap2)
        res_x = table_x + table_w + int(gap2_in * ppi)
        res_w = int(col_res_in * ppi)

        # --- VERTICAL POSITIONS (Centered Vertically) ---
        # We assume a fixed reasonable height for rows to center them
        slider_h = int(3.5 * ppi)
        btn_h = int(6.0 * ppi)
        gap_v = int(3.5 * ppi)
        
        total_opt_h = slider_h + gap_v + btn_h
        opt_start_y = (screen_h - total_opt_h) // 2
        
        table_h = int(10.0 * ppi)
        table_gap_v = int(1.5 * ppi)
        total_table_h = (table_h * 2) + table_gap_v
        table_start_y = (screen_h - total_table_h) // 2
        
        res_start_y = (screen_h - btn_h) // 2

        # --- ASSIGN RECTS ---
        
        # Options Col: Slider
        self.slider_rect = pygame.Rect(opt_x, opt_start_y, opt_w, slider_h)
        
        # Options Col: Buttons
        row2_y = opt_start_y + slider_h + gap_v
        btn_spacing = int(0.5 * ppi)
        # Split 34 inches into 3 buttons with spacing
        avail_w = opt_w - (2 * btn_spacing)
        single_btn_w = avail_w // 3
        
        self.btn_size_rect = pygame.Rect(opt_x, row2_y, single_btn_w, btn_h)
        self.btn_score_rect = pygame.Rect(self.btn_size_rect.right + btn_spacing, row2_y, single_btn_w, btn_h)
        self.btn_edge_rect = pygame.Rect(self.btn_score_rect.right + btn_spacing, row2_y, single_btn_w, btn_h)

        # Table Col: Mini Tables
        self.p1_area_rect = pygame.Rect(table_x, table_start_y, table_w, table_h)
        self.p2_area_rect = pygame.Rect(table_x, self.p1_area_rect.bottom + table_gap_v, table_w, table_h)
        
        # Resume Col: Button
        self.start_btn_rect = pygame.Rect(res_x, res_start_y, res_w, btn_h)

        # --- UPDATE EXISTING PUCK VISUALS ---
        for p in self.menu_pucks:
            p.update_visuals(self.puck_size, constants.PUCK_COLORS[p.color_name])
            
        # Keep them confined during resizing
        for _ in range(10): 
            self._confine_pucks(self.menu_pucks_p1, self.p1_area_rect)
            self._confine_pucks(self.menu_pucks_p2, self.p2_area_rect)

    def _resize_window_to_fit(self):
        """Calculates total width based on specification and resizes window."""
        old_w = self.screen_w

        margin = old_w - (40 + int(self.last_length) * 12) * constants.PPI
        new_w = margin + (40 + int(self.length) * 12) * constants.PPI

        self.screen_w = new_w
        pygame.display.set_mode((new_w, self.screen_h), pygame.RESIZABLE)
        self.update_layout(new_w, self.screen_h)

    def _confine_pucks(self, pucks, rect):
        if rect.width <= 1: return
        
        g_left = constants.GUTTER_PADDING_LEFT
        g_y = constants.GUTTER_PADDING_Y
        ppi = constants.PPI

        min_x_in = (rect.left - g_left) / ppi
        max_x_in = (rect.right - g_left) / ppi
        min_y_in = (rect.top - g_y) / ppi
        max_y_in = (rect.bottom - g_y) / ppi

        # 1. Hard Wall Clamp
        for p in pucks:
            p.x_in = max(min_x_in + p.radius_in, min(p.x_in, max_x_in - p.radius_in))
            p.y_in = max(min_y_in + p.radius_in, min(p.y_in, max_y_in - p.radius_in))

        # 2. Iterative Separation (The "Push" Logic)
        for i in range(len(pucks)):
            p1 = pucks[i]
            for j in range(i + 1, len(pucks)):
                p2 = pucks[j]
                dx = p1.x_in - p2.x_in
                dy = p1.y_in - p2.y_in
                dist = math.hypot(dx, dy)
                min_dist = p1.radius_in + p2.radius_in
                
                if dist < min_dist:
                    if dist == 0: # Prevent division by zero
                        dx = 0.1
                        dist = 0.1
                    overlap = min_dist - dist
                    p1.x_in += (dx / dist) * (overlap * 0.5)
                    p1.y_in += (dy / dist) * (overlap * 0.5)
                    p2.x_in -= (dx / dist) * (overlap * 0.5)
                    p2.y_in -= (dy / dist) * (overlap * 0.5)

    def handle_event(self, event):
        m_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_btn_rect.collidepoint(m_pos): return "START"
            
            # --- Slider Logic ---
            if self.slider_rect.collidepoint(m_pos):
                self.dragging_slider = True
                self._update_slider_val(m_pos[0])
                return "SLIDER_UPDATE"

            if self.btn_size_rect.collidepoint(m_pos): self.puck_size = constants.PUCK_LARGE if self.puck_size == constants.PUCK_MEDIUM else constants.PUCK_MEDIUM
            if self.btn_score_rect.collidepoint(m_pos): self.target_score = 15 if self.target_score == 21 else 21
            if self.btn_edge_rect.collidepoint(m_pos): self.edging_enabled = not self.edging_enabled

            # Check puck clicks
            clicked_puck = self._get_puck_at(m_pos)
            if clicked_puck:
                self._handle_puck_click(clicked_puck)
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
                self._update_slider_val(m_pos[0])
                return "SLIDER_UPDATE"
            
            if self.selected_puck:
                self._drag_puck(m_pos)

        return None

    def _update_slider_val(self, mouse_x):
        """Calculates slider value and triggers resize if integer foot changes."""
        if self.slider_rect.width <= 0: return

        # Clamp mouse X to slider rect
        m_x = max(self.slider_rect.left, min(mouse_x, self.slider_rect.right))
        
        # Calculate ratio
        ratio = (m_x - self.slider_rect.left) / self.slider_rect.width
        
        # Update continuous length (for smooth handle movement)
        self.length = self.min_len + (ratio * (self.max_len - self.min_len))
        
        # Puck size logic
        if self.last_length < 15 and int(self.length) >= 15: 
            self.puck_size = constants.PUCK_LARGE
        elif self.last_length > 14 and int(self.length) <= 14: 
            self.puck_size = constants.PUCK_MEDIUM
        
        # Check for Integer Change
        if int(self.length) != self.last_length:
            self._resize_window_to_fit()
            self.last_length = int(self.length)

    def _handle_puck_click(self, clicked_puck):
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

    def _drag_puck(self, m_pos):
        limit_rect = self.p1_area_rect if self.selected_puck.menu_group == P1 else self.p2_area_rect
        g_left = constants.GUTTER_PADDING_LEFT
        g_y = constants.GUTTER_PADDING_Y
        ppi = constants.PPI
        
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
        if len(self.throw_history) > 3: self.throw_history.pop(0)

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
        ppi = constants.PPI
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

    def get_handle_x(self):
        if self.slider_rect.width == 0: return self.slider_rect.left
        ratio = (self.length - self.min_len) / (self.max_len - self.min_len)
        return self.slider_rect.left + (self.slider_rect.width * ratio)
    
    def _draw_btn(self, screen, rect, text):
        pygame.draw.rect(screen, WOOD_LIGHT, rect, border_radius=8)
        lbl = self.btn_font.render(text, True, BLACK)
        screen.blit(lbl, lbl.get_rect(center=rect.center))

    def _draw_practice_table(self, screen, rect):
        shadow_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 60)) 
        screen.blit(shadow_surf, (rect.x + 4, rect.y + 4))
        pygame.draw.rect(screen, constants.WOOD_LIGHT, rect)

    def update_physics(self):
        g_left = constants.GUTTER_PADDING_LEFT
        g_y = constants.GUTTER_PADDING_Y
        ppi = constants.PPI

        def get_constraints(rect):
            if rect.width <= 0: return (0,0,0,0)
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

    def update_fonts(self):
        scale = constants.PPI / 10.0
        self.small_label_font = pygame.font.SysFont("arial", int(18 * scale), bold=True)
        self.btn_font = pygame.font.SysFont("arial", int(14 * scale), bold=True)
        self.font = pygame.font.SysFont("arial", int(20 * scale), bold=True)

    def draw(self, screen):
        self.update_fonts()
        self.update_physics()
        screen.fill(WOOD_DARK)
        
        # --- Labels ---
        lbl_y = self.slider_rect.top - int(1.5 * constants.PPI)
        len_lbl = self.small_label_font.render(f"Table Length: {int(self.length)} Ft", True, WHITE)
        screen.blit(len_lbl, len_lbl.get_rect(center=(self.slider_rect.centerx, lbl_y)))
        
        # --- Slider ---
        track_rect = pygame.Rect(self.slider_rect.left, self.slider_rect.centery - 4, self.slider_rect.width, 8)
        pygame.draw.rect(screen, (100, 50, 0), track_rect, border_radius=4)
        pygame.draw.circle(screen, WOOD_LIGHT, (int(self.get_handle_x()), int(self.slider_rect.centery)), self.handle_radius)
        
        # --- Buttons ---
        self._draw_btn(screen, self.btn_size_rect, "Medium Pucks" if self.puck_size == constants.PUCK_MEDIUM else "Large Pucks")
        self._draw_btn(screen, self.btn_score_rect, f"Game to {self.target_score}")
        self._draw_btn(screen, self.btn_edge_rect, "Edge for 4" if self.edging_enabled else "Edge for 3")

        # --- Zones ---
        self._draw_practice_table(screen, self.p1_area_rect)
        self._draw_practice_table(screen, self.p2_area_rect)

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
            p.update_visuals(self.puck_size, constants.PUCK_COLORS[p.color_name])
            p.draw(screen)