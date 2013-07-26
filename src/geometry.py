# warning, this is painfully slow
from pymunk import Vec2d

from itertools import starmap,product
from util import *

def side_of_line( p, xy0, xy1 ):
    p = Vec2d(p)
    xy0 = Vec2d(xy0)
    xy1 = Vec2d(xy1)
    d = (xy1-xy0).normalized()
    n = d.perpendicular_normal()
    return sign( (p-xy0).dot( n ) )

def inside_convex_polygon( p, vs ):
    rv = set(starmap( partial( side_of_line, p ), closed_circle_pairs(vs) ))
    if 0 in rv:
        rv.remove(0)
    return len(rv) == 1

def cross_2d( v, w ):
    return v.x * w.y - v.y * w.x

def line_segments_cross( a, b ):
    a0, a1 = a
    b0, b1 = b
    p = Vec2d(a0)
    r = Vec2d(a1) - p
    q = Vec2d(b0)
    s = Vec2d(b1) - q
    rxs = cross_2d(r,s)
    if abs(rxs) > 0.01:
        t = cross_2d(q-p, s) / rxs
        u = cross_2d(q-p, r) / rxs
        if (0 <= t <= 1) and (0 <= u <= 1):
            return p + r * t
    return None
    
def convex_polygons_overlap( xs, bs ):
    for a in xs:
        if inside_convex_polygon( a, bs ):
            return True
    for b in bs:
        if inside_convex_polygon( b, xs ):
            return True
    for line_seg in closed_circle_pairs( xs ):
        for other_line_seg in closed_circle_pairs( bs ):
            if line_segments_cross( line_seg, other_line_seg ):
                return True
    return False
