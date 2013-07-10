from pymunk import Vec2d

from physics import closed_circle_pairs

import physics
import graphics

import math
from itertools import starmap
from operator import attrgetter

from util import almost_equal, vectors_almost_equal, round_vector

import copy

from collections import OrderedDict

import sys

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
        return "<edge {0} to {1} ({2}, {3})>".format( tuple(round_vector(self.a,d=1)), tuple(round_vector(self.b,d=1)), self.length, self.angle_degrees )

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

class Block (object):
    def __init__(self):
        self.collision_shapes = []

    def register_shape(self, shape):
        self.collision_shapes.append( shape )

    def clone(self):
        # TODO refactor out this -- very inconvenient with ducking
        return copy.copy( self )
        
class PolygonBlock (Block):
    def __init__(self, vertices):
        super( PolygonBlock, self ).__init__()
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

    def create_collision_shape(self, extra_info = None, origin = None):
        return physics.ConvexPolygonShape( *self.vertices, extra_info = extra_info, origin = origin )

    def __repr__(self):
        return "<{0}>".format( "-".join( [ repr(round_vector((x,y),d=1)) for x,y in self.vertices] ) )

    def create_image(self):
        return self.image_name

class QuadBlock (PolygonBlock):
    def __init__(self, side_length):
        super( QuadBlock, self ).__init__( generate_square_vertices( side_length ) )
        self.image_name = "element_red_square.png"

    def __repr__(self):
        return "<{0}>".format( "-".join( [ repr((x,y)) for x,y in self.vertices] ) )

class IntegerMap (object):
    def __init__(self):
        self.d = OrderedDict()
        self.next_index = 0
    def append(self, value):
        self.d[ self.next_index ] = value
        self.next_index += 1
    def __iter__(self):
        for v in self.d.values():
            yield v
    def indexed(self):
        for k, v in self.d.items():
            yield (k,v)
    def __getitem__(self, index):
        return self.d[ index ]
    def __repr__(self):
        return "<IntegerMap {0}>".format( str(self.d.items()) )
    def __delitem__(self, index):
        del self.d[ index ]
    def __len__(self):
        return len(self.d)

class BlockStructure (object):
    def __init__(self, block):
        self.blocks = IntegerMap()
        self.free_edge_indices = []
        self.add_block( block )

    def add_block(self, block):
        index = self.blocks.next_index
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

    def extract_connections_map(self):
        rv = {}
        for index, block in self.blocks.indexed():
            rv[ index ] = dict(block.connections)
        return rv

    def extract_connections(self):
        rv = []
        for block_index, c in self.extract_connections_map().items():
            for local_index, connected in c.items():
                a = (block_index, local_index)
                assert a != connected
                if a < connected:
                    rv.append( (a,connected) )
        return rv

    def attach(self, index, block, block_edge_index ):
        block_index, edge_index = index
        local_edge = self.edge( index )
        delta_deg = - (180.0 + block.edges[ block_edge_index ].angle_degrees - local_edge.angle_degrees)
        block = block.clone()
        block.rotate_degrees( delta_deg )
        local_edge = self.edge( index )
        block.translate( - ( block.edges[ block_edge_index ].a - local_edge.b ) )
        local_edge = self.edge( index )
        if self.overlaps( block ):
            raise IllegalOverlapException()
        block.free_edge_indices.remove( block_edge_index )
        foreign_block_index = self.blocks.next_index
        local_edge = self.edges[ edge_index ]
        foreign_edge = block.edges[ block_edge_index ]
        self.add_block( block )
        for local_block_index, local_edge_index in self.free_edge_indices:
            local_edge = self.edge( (local_block_index,local_edge_index) )
            if local_block_index == foreign_block_index:
                continue
            for foreign_edge_index, foreign_edge in indexed_zip(block.edges):
                if local_edge.overlaps( foreign_edge ):
                    self.blocks[ local_block_index ].free_edge_indices.remove( local_edge_index )
                    block.connections[ foreign_edge_index ] = (local_block_index, local_edge_index)
                    self.blocks[ local_block_index ].connections[ local_edge_index ] = (foreign_block_index, foreign_edge_index)
                    self.free_edge_indices.remove( (local_block_index,local_edge_index) )
                    self.free_edge_indices.remove( (foreign_block_index,foreign_edge_index) )
        return foreign_block_index
    
    def remove_block(self, index):
        # TODO ensure connections consistent etc.
        block = self.blocks[ index ]
        del self.blocks[ index ]
        # TODO ensure connected, and return both the block and any detached parts
        try:
            s = self.sprite_structure
        except AttributeError:
            s = None
        if s:
            s.remove_sprite( block.sprite )
        for collision_shape in block.collision_shapes:
            sim = collision_shape.thing.sim
            collision_shape.thing.shapes.remove( collision_shape )
            sim.remove( collision_shape )

    def create_collision_shape(self):
        rv = []
        for index, block in self.blocks.indexed():
            rv.append(block.create_collision_shape( extra_info = index, origin = block ))
        return physics.CompositeShape( *rv )

    def centroid(self):
        return self.create_collision_shape().centroid()

    def create_sprite_structure(self, thing, layer):
        self.sprite_structure = s = graphics.SpriteStructure( thing, layer )
        c = self.centroid()
        for block in self.blocks:
            block.sprite = s.add_sprite( block.create_image(), block.translation - c )

def filter_connections( connections, block_indices ):
    def check_connection( connection ):
        (a,_), (b,_) = connection
        return (a not in block_indices) and (b not in block_indices)
    return filter( check_connection, connections )

def blocks_in_connections( connections ):
    rv = set()
    for (a,_), (b,_) in connections:
        rv.add( a )
        rv.add( b )
    return tuple(rv)

def explore_connections( connections, start ):
    seen = set( [start] )
    changed = True
    rv = []
    while changed:
        changed = False
        for connection in connections:
            (a,_), (b,_) = connection
            a_new = a not in seen
            b_new = b not in seen
            if a_new and not b_new:
                changed = True
                seen.add( a_new )
                rv.append( connection )
            if b_new and not a_new: 
                changed = True
                seen.add( b_new )
                rv.append( connection )
    return rv
        
def partition_connections( connections ):
    rv = []
    while connections:
        start_block = blocks_in_connections( connections )[0]
        connections_chunk = explore_connections( connections, start_block )
        blocks_in_chunk = set( blocks_in_connections( connections_chunk ) )
        blocks_in_chunk.add( start_block )
        connections = filter_connections( connections, blocks_in_chunk )
        rv.append( ( tuple( blocks_in_chunk ), connections_chunk ) )
    return rv

def partition_connections_removing_blocks( connections, block_indices ):
    return partition_connections( filter_connections( connections, block_indices ) )
