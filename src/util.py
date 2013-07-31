import math
from pymunk import Vec2d

from functools import partial
from itertools import starmap

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

def ignore_arguments( f ):
    return lambda *args, **kwargs : f()

def sign( n ):
    if n > 0:
        return 1
    if n < 0:
        return -1
    return 0

def closed_circle( l ):
    it = l.__iter__()
    first_element = it.next()
    yield first_element
    for element in it:
        yield element
    yield first_element

def successive_ntuples( n, l ):
    rv = []
    it = l.__iter__()
    for i in range(n):
        rv.append( it.next() )
    while True:
        yield tuple(rv)
        rv.pop(0)
        rv.append( it.next() )

def successive_pairs( l ):
    return successive_ntuples(2, l)

def successive_triples( l ):
    return successive_ntuples(3, l)

def closed_circle_pairs( l ):
    return successive_pairs( closed_circle( l ) )

def generate_regular_polygon_vertices(n, r = 1.0, start_angle = None):
    step = math.pi * 2.0 / float(n)
    if not start_angle:
        start_angle = - 0.5 * step
    if start_angle == None:
        start_angle = 0.5 * step
    for i in range(n):
        angle = start_angle + i * step
        yield r * math.cos( angle ), r * math.sin( angle )

def radius_for_side_length(n, side_length):
    a, b = list(generate_regular_polygon_vertices(n,1.0))[:2]
    ratio = side_length / (Vec2d(a)-Vec2d(b)).get_length()
    return ratio

def generate_square_vertices(s):
    h = 0.5 * s
    return [(-h,-h),(h,-h),(h,h),(-h,h)]

def indexed_zip( l ):
    return zip( range(len(l)), l )

def lerp( p, a, b ):
    if p <= 0.0:
        return a
    if p >= 1.0:
        return b
    return p * b + (1.0-p) * a

def vector_lerp( p, a, b ):
    return starmap( partial(lerp, p), zip(a,b) )

def key_and_value_dictmap( f, d ):
    return { f(k): f(v) for (k,v) in d.items() }

def recursively_untuple( xs ):
    if isinstance( xs, tuple ) or isinstance( xs, list ):
        return list(map(recursively_untuple, xs))
    elif isinstance( xs, dict ):
        return key_and_value_dictmap( recursively_untuple, xs )
    else:
        return xs

class Hookable (object):
    def __init__(self):
        self.hooks = {}
    def add_hook(self, obj, f ):
        try:
            self.hooks[ obj ].append( f )
        except KeyError:
            self.hooks[ obj ] = [ f ]
    def add_anonymous_hook(self, f ):
        self.add_hook( None, f )
    def remove_hooks(self, obj ):
        try:
            del self.hooks[ obj ]
        except KeyError:
            pass
    def __call__(self, *args, **kwargs):
        for hooks in self.hooks.values():
            for hook in hooks:
                hook(*args, **kwargs)

def degrees_sub( a, b ):
    return (a - b) % 360.0
