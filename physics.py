import math

# Constants
MU = 1.3271244e20  # Sun's gravitational parameter

def get_planet_state(p, day):
    """Calculates planet position (x, y) and velocity (vx, vy)."""
    if not p.get('period') or p['period'] == 0:
        return {'x': 0, 'y': 0, 'vx': 0, 'vy': 0}
    
    t = day * 86400
    n = (2 * math.pi) / p['period']
    M = (p['theta0'] + (n * t)) % (2 * math.pi)
    
    # Solve Kepler's Equation (Newton's Method)
    E = M
    iterations = 12 if p.get('e', 0) > 0.5 else 3
    for _ in range(iterations):
        E = E - (E - p['e'] * math.sin(E) - M) / (1 - p['e'] * math.cos(E))
    
    # True Anomaly & Radius
    nu = 2 * math.atan2(math.sqrt(1 + p['e']) * math.sin(E/2), math.sqrt(1 - p['e']) * math.cos(E/2))
    r = p['a'] * (1 - p['e'] * math.cos(E))
    
    # Position in Heliocentric Coordinates
    x = r * math.cos(nu + p['omega'])
    y = r * math.sin(nu + p['omega'])

    # Velocity Vector Calculation
    e_term = (1 - p['e']**2)
    if e_term <= 0 or r == 0:
        return {'x': x, 'y': y, 'vx': 0, 'vy': 0}

    h = math.sqrt(MU * p['a'] * e_term)
    vx = (x * h * p['e'] * math.sin(nu)) / (r * p['a'] * e_term) - (h * math.sin(nu + p['omega'])) / r
    vy = (y * h * p['e'] * math.sin(nu)) / (r * p['a'] * e_term) + (h * math.cos(nu + p['omega'])) / r

    return {'x': x, 'y': y, 'vx': vx, 'vy': vy}

def solve_trajectory(p1, p2, day, accel, dv_limit):
    """Calculates the time to intercept a moving target."""
    start_sec = day * 86400
    s1 = get_planet_state(p1, day)
    s2_now = get_planet_state(p2, day)
    
    # Initial Euclidean distance
    dist = math.sqrt((s2_now['x'] - s1['x'])**2 + (s2_now['y'] - s1['y'])**2)
    
    # Iterative Intercept Solver
    # We solve for where the planet WILL be at the end of the burn
    t_sec = 0
    for _ in range(8):
        t_sec = 2 * math.sqrt(dist / accel) # Brachistochrone base time
        s2_f = get_planet_state(p2, day + (t_sec / 86400))
        dist = math.sqrt((s2_f['x'] - s1['x'])**2 + (s2_f['y'] - s1['y'])**2)

    # Relative Velocity Matching (Delta-V cost)[cite: 5, 6]
    s2_f = get_planet_state(p2, day + (t_sec / 86400))
    rel_vel = math.sqrt((s2_f['vx'] - s1['vx'])**2 + (s2_f['vy'] - s1['vy'])**2)
    min_total_t = t_sec + (rel_vel / accel)
    total_dv = (accel * min_total_t) / 1000

    # Fuel-Limited Trajectory (Realistic Time)
    realistic_t = min_total_t
    if 0 < dv_limit < total_dv:
        v_max = (dv_limit * 1000) / 2
        t_burn = (2 * v_max) / accel
        d_burn = accel * (v_max / accel)**2
        realistic_t = (t_burn + (dist - d_burn) / v_max) + (rel_vel / accel)

    return {
        'days': realistic_t / 86400,
        'dv_required': total_dv,
        'distance_au': dist / 1.496e11
    }