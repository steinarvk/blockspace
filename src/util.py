import math

def degrees_to_radians( degrees ):
    return math.pi * degrees / 180.0

def radians_to_degrees( radians ):
    return 180.0 * radians / math.pi

def polar_radians( theta_radians, r ):
    return r * math.cos( theta_radians ), r * math.sin( theta_radians )

def polar_degrees( theta_degrees, r ):
    return polar_radians( degrees_to_radians( theta_degrees ), r )
