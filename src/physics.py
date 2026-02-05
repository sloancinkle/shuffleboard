import math
import random
from .constants import MIN_SPEED, STATE_SELECTED, STATE_ON_BOARD, STATE_THROWN

def move_puck_substep(puck, steps):
    """
    Moves the puck a fraction of its velocity. 
    We call this multiple times per frame (e.g., 8 times).
    """
    if puck.is_moving:
        # Move only 1/8th of the distance
        puck.x_in += puck.dx / steps
        puck.y_in += puck.dy / steps

def apply_friction(puck, friction):
    """
    Applies friction / braking.
    We call this ONLY ONCE per frame at the end.
    """
    if puck.is_moving:
        puck.dx *= friction
        puck.dy *= friction
        
        speed = math.hypot(puck.dx, puck.dy)
        if speed < MIN_SPEED:
            puck.dx = 0
            puck.dy = 0
            puck.is_moving = False
            return False
        return True
    return False

def resolve_boundary_bounce(puck, min_x, max_x, min_y, max_y, bounce_factor=-0.6):
    """
    Keeps puck within rectangular bounds by bouncing off walls.
    """
    if puck.x_in < min_x + puck.radius_in:
        puck.x_in = min_x + puck.radius_in
        puck.dx *= bounce_factor
    elif puck.x_in > max_x - puck.radius_in:
        puck.x_in = max_x - puck.radius_in
        puck.dx *= bounce_factor

    if puck.y_in < min_y + puck.radius_in:
        puck.y_in = min_y + puck.radius_in
        puck.dy *= bounce_factor
    elif puck.y_in > max_y - puck.radius_in:
        puck.y_in = max_y - puck.radius_in
        puck.dy *= bounce_factor

def resolve_rect_container(puck, min_x, max_x, min_y, max_y):
    """
    Strictly traps a puck inside a specific rectangle (used for menu boxes).
    """
    bounce = -0.6
    if puck.x_in < min_x + puck.radius_in:
        puck.x_in = min_x + puck.radius_in
        puck.dx *= bounce
    elif puck.x_in > max_x - puck.radius_in:
        puck.x_in = max_x - puck.radius_in
        puck.dx *= bounce

    if puck.y_in < min_y + puck.radius_in:
        puck.y_in = min_y + puck.radius_in
        puck.dy *= bounce
    elif puck.y_in > max_y - puck.radius_in:
        puck.y_in = max_y - puck.radius_in
        puck.dy *= bounce

def check_puck_collision(p1, p2):
    dx = p1.x_in - p2.x_in
    dy = p1.y_in - p2.y_in
    dist = math.hypot(dx, dy)
    min_dist = p1.radius_in + p2.radius_in
    
    if dist < min_dist:
        # 1. Improved Angle Calculation
        if dist == 0: 
            angle = random.uniform(0, 2 * math.pi)
            dist = 0.001
        else:
            angle = math.atan2(dy, dx)
            
        overlap = min_dist - dist
        nx = math.cos(angle)
        ny = math.sin(angle)

        if p1.state == STATE_SELECTED:
            _apply_kick(p2, nx, ny, overlap, invert=True)
            return
        if p2.state == STATE_SELECTED:
            _apply_kick(p1, nx, ny, overlap, invert=False)
            return

        # 2. Relative Velocity along the normal
        # This is the 'Closing Velocity'
        rvx = p1.dx - p2.dx
        rvy = p1.dy - p2.dy
        vel_along_normal = (rvx * nx) + (rvy * ny)

        # IMPORTANT: Only resolve if pucks are moving TOWARD each other
        # If they are already moving apart, don't apply another bounce
        if vel_along_normal > 0:
            return

        # 3. Position Correction (Anti-clumping)
        # We use a 'slop' and 'percent' to prevent jitter
        percent = 0.8 # how much of the overlap to fix
        slop = 0.01   # allow a tiny bit of overlap to prevent oscillation
        correction = (max(overlap - slop, 0) / 2) * percent
        
        p1.x_in += nx * correction
        p1.y_in += ny * correction
        p2.x_in -= nx * correction
        p2.y_in -= ny * correction

        # 4. Impulse Resolution (The "Crunch")
        # Increase restitution for a more "bouncy" arcade feel
        restitution = 0.8 
        j = -(1 + restitution) * vel_along_normal
        j /= 2 # Assuming equal mass
        
        # Apply the impulse
        p1.dx += j * nx
        p1.dy += j * ny
        p2.dx -= j * nx
        p2.dy -= j * ny
        
        # Wake up both pucks
        p1.is_moving = True
        p2.is_moving = True

def _apply_kick(puck, nx, ny, overlap, invert=False):
    direction = -1 if invert else 1
    puck.x_in += nx * overlap * direction
    puck.y_in += ny * overlap * direction
    
    kick_power = 2.5
    puck.dx += nx * (overlap * kick_power) * direction
    puck.dy += ny * (overlap * kick_power) * direction
    puck.is_moving = True
    if puck.state == STATE_ON_BOARD: 
        puck.state = STATE_THROWN

def resolve_static_overlap(p1, p2):
    """Separates two pucks equally."""
    dx = p1.x_in - p2.x_in
    dy = p1.y_in - p2.y_in
    dist = math.hypot(dx, dy)
    min_dist = p1.radius_in + p2.radius_in + 0.05
    
    if dist < min_dist:
        overlap = min_dist - dist
        if dist == 0: angle = 0
        else: angle = math.atan2(dy, dx)
        
        move_x = math.cos(angle) * (overlap / 2)
        move_y = math.sin(angle) * (overlap / 2)
        p1.x_in += move_x
        p1.y_in += move_y
        p2.x_in -= move_x
        p2.y_in -= move_y

def resolve_static_push(pusher, pushed):
    """Moves 'pushed' completely away from 'pusher' (used when dragging)."""
    dx = pushed.x_in - pusher.x_in
    dy = pushed.y_in - pusher.y_in
    dist = math.hypot(dx, dy)
    min_dist = pusher.radius_in + pushed.radius_in + 0.05
    
    if dist < min_dist:
        overlap = min_dist - dist
        if dist == 0: angle = 0
        else: angle = math.atan2(dy, dx)
        
        pushed.x_in += math.cos(angle) * overlap
        pushed.y_in += math.sin(angle) * overlap