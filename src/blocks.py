from pymunk import Vec2d

from physics import closed_circle_pairs

import physics
import graphics

import math
from itertools import starmap
from operator import attrgetter

from util import *

import copy

from collections import OrderedDict

import sys

class IllegalOverlapException (Exception):
    pass

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

    def midpoint(self):
        return (self.a+self.b)*0.5

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
        self.components = []

    def attach_components(self, thing):
        for component in self.components:
            component.attach( thing )
    
    def detach_components(self, thing):
        for component in self.components:
            component.detach( thing )

    def area(self):
        return self.create_collision_shape().area()

    def register_shape(self, shape):
        self.collision_shapes.append( shape )

    def clone(self):
        # TODO refactor out this -- very inconvenient with ducking
        return copy.copy( self )

    def centroid(self):
        return self.create_collision_shape().centroid()

    @property
    def position(self):
        return self.thing.position + self.translation.rotated( self.thing.angle_radians )

    @property
    def angle_degrees(self):
        return self.thing.angle_degrees + self.rotation_degrees

    @property
    def angle_radians(self):
        return degrees_to_radians( self.angle_degrees )

    @property
    def velocity(self):
        rel = self.translation
        r = rel.length
        b = rel.rotated_degrees( self.thing.angle_degrees + 90.0 ).normalized()
        rv = b * (self.thing.angular_velocity_radians * r)
        av = self.thing.velocity
        return av + rv

    @property
    def thing(self):
        for collision_shape in self.collision_shapes:
            return collision_shape.thing
        return None

        
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
        return "<PolygonBlock {0}>".format( "-".join( [ repr(round_vector((x,y),d=1)) for x,y in self.vertices] ) )

    def create_sprite(self):
        rv = graphics.cocos.sprite.Sprite( self.image_name )
        rv.color = self.colour
        return rv

class QuadBlock (PolygonBlock):
    def __init__(self, side_length):
        super( QuadBlock, self ).__init__( generate_square_vertices( side_length ) )
        self.image_name = "myblockgray.png"
        self.colour = 255,255,255

    def __repr__(self):
        return "<QuadBlock {0}>".format( "-".join( [ repr((x,y)) for x,y in self.vertices] ) )

class OctaBlock (PolygonBlock):
    def __init__(self, side_length):
        super( OctaBlock, self ).__init__( generate_regular_polygon_vertices( 8, radius_for_side_length( 8, side_length ) ) )
        self.image_name = "myoctagray.png"
        self.colour = 255,255,255

    def __repr__(self):
        return "<OctaBlock {0}>".format( "-".join( [ repr((x,y)) for x,y in self.vertices] ) )

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

    def area(self):
        return sum( [ block.area() for block in self.blocks ] )

    def translate(self, xy):
        for block in self.blocks:
            block.translate( xy )

    def zero_centroid(self):
        self.translate( -self.centroid() )
        

    def add_block(self, block):
        index = self.blocks.next_index
        self.free_edge_indices.extend(list(map( lambda edge_index : (index,edge_index), range(len(block.edges)))))
        self.blocks.append( block )

    def any_block(self):
        try:
            index, block = self.blocks.indexed().next()
            return block
        except:
            return None

    def any_block_index(self):
        try:
            index, block = self.blocks.indexed().next()
            return index
        except:
            return None

    @property
    def edges(self):
        rv = []
        for block in self.blocks:
            rv.extend( block.edges )
        return rv

    def get_components(self, check = lambda component : True):
        rv = []
        for block in self.blocks:
            rv.extend( [ x for x in block.components if check(x) ] )
        return rv

    def edge(self, index):
        block_index, edge_index = index
        return self.blocks[ block_index ].edge( edge_index )

    def overlaps(self, block):
        # TODO nondegenerate overlap check
        return False
    
    def connectivity_set_of(self, index):
        q = [index]
        rv = set()
        while q:
            x = q.pop(0)
            rv.add(x)
            for (i,_) in self.blocks[x].connections.values():
                if (i not in rv) and (i not in q):
                    q.append(i)
        return rv

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
#        block = block.clone()
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
        # TODO ensure centroid is correct, and adjust sprites
        block = self.blocks[ index ]
        for connection in block.connections.values():
            other_block_index, other_edge_index = connection
            other_block = self.blocks[ other_block_index ]
            other_block.free_edge_indices.append( other_edge_index )
            self.free_edge_indices.append( connection )
            assert other_block.connections[ other_edge_index ][0] == index
            del other_block.connections[ other_edge_index ]
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
        return block

    def create_collision_shape(self):
        rv = []
        for index, block in self.blocks.indexed():
            rv.append(block.create_collision_shape( extra_info = index, origin = block ))
        return physics.CompositeShape( *rv )

    def clear_collision_shape(self):
        for index, block in self.blocks.indexed():
            for collision_shape in block.collision_shapes:
                sim = collision_shape.thing.sim
                sim.remove( collision_shape )
            block.collision_shapes = []

    def centroid(self):
        return self.create_collision_shape().centroid()

    def create_sprite_structure(self, **kwargs):
        s = graphics.SpriteStructure( **kwargs )
        c = self.centroid()
        for block in self.blocks:
            block_pos = block.translation - c 
            s.add_sprite( block.create_sprite(), block_pos, rotation = block.rotation_degrees, key = block )
            for component in block.components:
                try:
                    component.position
                except AttributeError:
                    continue
                s.add_sprite( component.sprite, block_pos + component.relative_position, z = -1 )
        return s

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
