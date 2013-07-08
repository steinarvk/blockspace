from pymunk import Vec2d

from physics import closed_circle_pairs

import physics
import graphics

import math
from itertools import starmap

from util import almost_equal, vectors_almost_equal, round_vector

class IllegalOverlapException (Exception):
    pass

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

def indexed_zip( l ):
    return zip( range(len(l)), l )

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

    def overlaps(self, edge):
        if vectors_almost_equal(self.a,edge.a) and vectors_almost_equal(self.b,edge.b):
            return True
        if vectors_almost_equal(self.a,edge.b) and vectors_almost_equal(self.b,edge.a):
            return True
        return False
    
    @property
    def angle_degrees(self):
        return (self.b - self.a).rotated_degrees(-90).get_angle_degrees() % 360.0
        
class PolygonBlock (object):
    def __init__(self, vertices):
        self.vertices = map( Vec2d, vertices )
        self.free_edge_indices = range(len(self.edges))
        self.connections = {}
        self.rotation_degrees = 0.0
        self.translation = Vec2d(0,0)

    @property
    def edges(self):
        return list(starmap( Edge, closed_circle_pairs( self.vertices ) ))

    def edge(self, index):
        return self.edges[index]

    def rotate_radians(self, delta_radians):
        self.rotation_degrees += radians_to_degrees( delta_radians )
        for v in self.vertices:
            v.rotate( delta_radians )
        return self

    def rotate_degrees(self, delta_degrees):
        self.rotation_degrees += delta_degrees
        for v in self.vertices:
            v.rotate_degrees( delta_degrees )
        return self

    def translate(self, xy):
        xy = Vec2d(xy)
        self.translation += xy
        self.vertices = map( lambda x : x + xy, self.vertices )
        return self

    def create_collision_shape(self):
        return physics.ConvexPolygonShape( *self.vertices )
        
    def clone(self):
        # TODO refactor out this -- very inconvenient with ducking
        return PolygonBlock( self.vertices )
        
    def __repr__(self):
        return "<{0}>".format( "-".join( [ repr((x,y)) for x,y in self.vertices] ) )

    def create_image(self):
        return self.image_name

class QuadBlock (PolygonBlock):
    def __init__(self, side_length):
        super( QuadBlock, self ).__init__( generate_square_vertices( side_length ) )
        self.image_name = "element_red_square.png"

    def __repr__(self):
        return "<{0}>".format( "-".join( [ repr((x,y)) for x,y in self.vertices] ) )

class BlockStructure (object):
    def __init__(self, block):
        self.blocks = []
        self.free_edge_indices = []
        self.add_block( block )

    def add_block(self, block):
        index = len(self.blocks)
        self.free_edge_indices.extend(list(map( lambda edge_index : (index,edge_index), range(len(block.edges)))))
        self.blocks.append( block )

    @property
    def edges(self):
        rv = []
        for block in self.blocks:
            rv.extend( block.edges )
        return rv

    def edge(self, index):
        block_index, edge_index = index
        return self.blocks[ block_index ].edge( edge_index )

    def overlaps(self, block):
        # TODO nondegenerate overlap check
        return False

    def attach(self, index, block, block_edge_index ):
        block_index, edge_index = index
        delta_deg = block.edges[ block_edge_index ].angle_degrees - self.edges[ edge_index ].angle_degrees
        block = block.clone()
        print "rotating", delta_deg
        block.rotate_degrees( -delta_deg )
        print "translating",block.edges[ block_edge_index ].a - self.edges[ edge_index].b
        block.translate( block.edges[ block_edge_index ].a - self.edges[ edge_index].b )
        if self.overlaps( block ):
            raise IllegalOverlapException()
        block.free_edge_indices.remove( block_edge_index )
        foreign_block_index = len( self.blocks )
        local_edge = self.edges[ edge_index ]
        foreign_edge = block.edges[ block_edge_index ]
        self.add_block( block )
        for local_block_index, local_edge_index in self.free_edge_indices:
            local_edge = self.edge( (local_block_index,local_edge_index) )
            if local_block_index == foreign_block_index:
                continue
            for foreign_edge_index, foreign_edge in indexed_zip(block.edges):
                if local_edge.overlaps( foreign_edge ):
                    print local_block_index, local_edge_index
                    print "local edge", (local_block_index,local_edge_index), local_edge, "overlaps", foreign_edge_index, foreign_edge
                    self.blocks[ local_block_index ].free_edge_indices.remove( local_edge_index )
                    block.connections[ foreign_edge_index ] = (local_block_index, local_edge_index)
                    self.blocks[ local_block_index ].connections[ local_edge_index ] = (foreign_block_index, foreign_edge_index)
                    self.free_edge_indices.remove( (local_block_index,local_edge_index) )
                    self.free_edge_indices.remove( (foreign_block_index,foreign_edge_index) )
        return foreign_block_index

    def create_collision_shape(self):
        return physics.CompositeShape( *(block.create_collision_shape() for block in self.blocks) )

    def create_sprite_structure(self, thing, layer):
        s = graphics.SpriteStructure( thing, layer )
        for block in self.blocks:
            s.add_sprite( block.create_image(), block.translation)
