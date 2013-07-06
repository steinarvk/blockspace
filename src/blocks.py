from pymunk import Vec2d

from physics import closed_circle_pairs

import math
from itertools import starmap

from util import almost_equal

def generate_regular_polygon_vertices(n, r = 1.0, start_angle = None):
    step = math.pi * 2.0 / float(n)
    if start_angle == None:
        start_angle = 0.5 * step
    for i in range(n):
        angle = start_angle + i * step
        yield r * math.cos( angle ), r * math.sin( angle )

def generate_square_vertices(s):
    h = 0.5 * s
    return [(-h,-h),(h,-h),(h,h),(-h,h)]

class Edge (object):
    def __init__(self, a, b):
        self.a = Vec2d(a)
        self.b = Vec2d(b)

    @property
    def length(self):
        return self.a.get_distance( self.b )

    def __repr__(self):
        return "<edge {0} to {1} ({2}, {3})>".format( tuple(self.a), tuple(self.b), self.length, self.angle_degrees )

    def matches(self, edge):
        return almost_equal( self.length, edge.length )
    
    @property
    def angle_degrees(self):
        return (self.b - self.a).rotated_degrees(-90).get_angle_degrees() % 360.0
        
        

class PolygonBlock (object):
    def __init__(self, vertices):
        self.vertices = map( Vec2d, vertices )
        self.free_edge_indices = range(len(self.edges))

    @property
    def edges(self):
        return list(starmap( Edge, closed_circle_pairs( self.vertices ) ))

    def rotate_radians(self, delta_radians):
        for v in self.vertices:
            v.rotate( delta_radians )
        return self

    def rotate_degrees(self, delta_degrees):
        for v in self.vertices:
            v.rotate_degrees( delta_degrees )
        return self

    def translate(self, xy):
        xy = Vec2d(xy)
        self.vertices = map( lambda x : x + xy, self.vertices )
        return self

    def create_collision_shape(self):
        return ConvexPolygonShape( *self.vertices )

class QuadBlock (PolygonBlock):
    def __init__(self, side_length):
        super( QuadBlock, self ).__init__( generate_square_vertices( side_length ) )
    def __repr__(self):
        return "<{0}>".format( "-".join( [ repr((x,y)) for x,y in self.vertices] ) )
