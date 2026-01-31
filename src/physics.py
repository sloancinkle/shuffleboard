import math
from .constants import MIN_SPEED, STATE_SELECTED, STATE_ON_BOARD, STATE_THROWN

def update_puck_movement(puck, friction):
    """
    Updates position based on velocity and applies friction.
    Returns True if the puck is still moving, False otherwise.
    """
    if puck.is_moving:
        puck.x_in += puck.dx
        puck.y_in += puck.dy
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
    """
    Detects and resolves collision between two pucks using elastic collision logic.
    Also handles 'kick' logic if one puck is being held (SELECTED).
    """
    dx = p1.x_in - p2.x_in
    dy = p1.y_in - p2.y_in
    dist = math.hypot(dx, dy)
    min_dist = p1.radius_in + p2.radius_in
    
    if dist < min_dist:
        if dist == 0: 
            angle = 0
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

        # Standard Elastic Collision
        move_x = nx * (overlap / 2)
        move_y = ny * (overlap / 2)
        p1.x_in += move_x
        p1.y_in += move_y
        p2.x_in -= move_x
        p2.y_in -= move_y
        
        rx = p1.dx - p2.dx
        ry = p1.dy - p2.dy
        vel_along_normal = (rx * nx) + (ry * ny)

        if vel_along_normal > 0: 
            return

        restitution = 0.9
        j = -(1 + restitution) * vel_along_normal
        j /= 2 
        
        ix = j * nx
        iy = j * ny
        
        p1.dx += ix
        p1.dy += iy
        p2.dx -= ix
        p2.dy -= iy
        
        p1.is_moving = True
        p2.is_moving = True
        
        if p1.state == STATE_ON_BOARD: p1.state = STATE_THROWN
        if p2.state == STATE_ON_BOARD: p2.state = STATE_THROWN

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