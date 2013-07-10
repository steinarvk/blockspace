import math
from pymunk import Vec2d

def degrees_to_radians( degrees ):
    return math.pi * degrees / 180.0

def radians_to_degrees( radians ):
    return 180.0 * radians / math.pi

def polar_radians( theta_radians, r ):
    return r * math.cos( theta_radians ), r * math.sin( theta_radians )

def polar_degrees( theta_degrees, r ):
    return polar_radians( degrees_to_radians( theta_degrees ), r )

def almost_equal( x, y, k = 0.0001 ):
    return abs( x - y ) <= k * max( 0.01, abs(x), abs(y) )

def almost_equal( x, y, k = 0.0001 ):
    return abs( x - y ) <= k * max( 0.01, abs(x), abs(y) )

def almost_leq( x, y, k = 0.0001 ):
    return x <= y + k * abs(y)

def almost_geq( x, y, k = 0.0001 ):
    return x >= y - k * abs(y)
    
def vectors_almost_equal(a, b, k = 0.001):
    return (Vec2d(a)-Vec2d(b)).get_length() <= k

def radians_almost_equal(a, b, k = 0.001):
    return vectors_almost_equal( Vec2d(math.cos(a),math.sin(a)), Vec2d(math.cos(b),math.sin(b)), k = k )

def degrees_almost_equal(a, b, k = 0.001):
    return radians_almost_equal( degrees_to_radians(a), degrees_to_radians(b), k = k )

def round_scalar( s, d = 1000000 ):
    return int(s * d) / float(d)

def round_vector( xy, d = 1000000 ):
    x, y = xy
    return Vec2d( round_scalar(x, d = d), round_scalar(y, d = d) )
