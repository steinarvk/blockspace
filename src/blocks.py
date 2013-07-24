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

from geometry import convex_polygons_overlap

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

    def point(self, x):
        assert 0 <= x <= 1
        return (self.a+self.b)*x

    def overlaps(self, edge):
        if vectors_almost_equal(self.a,edge.a) and vectors_almost_equal(self.b,edge.b):
            return True
        if vectors_almost_equal(self.a,edge.b) and vectors_almost_equal(self.b,edge.a):
            return True
        return False

    def almost_overlaps(self, edge, max_distance = 1.0):
        if vectors_almost_equal(self.a,edge.a,k=max_distance) and vectors_almost_equal(self.b,edge.b,k=max_distance):
            return True
        if vectors_almost_equal(self.a,edge.b,k=max_distance) and vectors_almost_equal(self.b,edge.a,k=max_distance):
            return True
        return False
    
    @property
    def angle_degrees(self):
        return (self.b - self.a).rotated_degrees(-90).get_angle_degrees() % 360.0

class Block (object):
    def __init__(self):
        self.collision_shapes = []
        self.components = []
        self.hp = self.max_hp = 10
        self.cockpit = False

    @staticmethod
    def load_data( data ):
        # will we ever need anything other than PolygonBlocks?
        return PolygonBlock.load_data( data )

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
        self.original_vertices = map( Vec2d, vertices )
        self.inner_vertices = map( lambda x : Vec2d(x) * 0.99, vertices )
        self.free_edge_indices = range(len(self.edges))
        self.connections = {}
        self.rotation_degrees = 0.0
        self.translation = Vec2d(0,0)
        self.sprite_scale = 1.0
        self.sprite_flipy = False

    def transformed_vertices(self):
        xs = map( Vec2d, self.original_vertices )
        for v in xs:
            v.rotate_degrees( self.rotation_degrees )
        xs = map( lambda x : x + self.translation, xs )
        return xs

    def transformed_inner_vertices(self):
        xs = map( Vec2d, self.inner_vertices )
        for v in xs:
            v.rotate_degrees( self.rotation_degrees )
        xs = map( lambda x : x + self.translation, xs )
        return xs

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

    def interiors_overlap(self, other):
        return convex_polygons_overlap( self.transformed_inner_vertices(), other.transformed_inner_vertices() )

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
        return graphics.create_sprite( self.sprite_info )

    @staticmethod
    def load_data( data ):
        rv = PolygonBlock( data["vertices"] )
        rv.hp = data["hp"]
        rv.max_hp = data["max-hp"]
        rv.cockpit = data["cockpit"]
        rv.inner_vertices = data["inner-vertices"]
        rv.sprite_info = data["sprite"]
        for f in (lambda : data["sprite-scale"], lambda : data["side-length"] / data["pixel-side-length"], lambda : 1):
            try:
                rv.sprite_scale = f()
                break
            except:
                pass
        return rv

    def dump_data(self):
        rv = {}
        rv["hp"] = self.hp
        rv["max-hp"] = self.max_hp
        rv["cockpit"] = self.cockpit
        rv["vertices"] = [ [x,y] for (x,y) in self.original_vertices ]
        rv["colour"] = list(self.colour)
        rv["inner-vertices"] = self.inner_vertices
        rv["sprite-scale"] = self.sprite_scale
        rv["sprite"] = self.sprite_info
        return recursively_untuple( rv )

    def dump_string(self):
        import yaml
        return yaml.dump( self.dump_data() )

    @staticmethod
    def load_string( s ):
        import yaml
        return PolygonBlock.load_data( yaml.safe_load( s ) )

    @staticmethod
    def load_file( fn ):
        with open( fn, "r" ) as f:
            return PolygonBlock.load_string( f.read() )

    def dump_file( self, fn ):
        with open( fn, "w" ) as f:
            f.write( self.dump_string() )
        

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
    def keys(self):
        return self.d.keys()
    def indexed(self):
        for k, v in self.d.items():
            yield (k,v)
    def __setitem__(self, index, value):
        self.d[ index ] = value
        if index >= self.next_index:
            self.next_index = index + 1
    def __getitem__(self, index):
        return self.d[ index ]
    def __repr__(self):
        return "<IntegerMap {0}>".format( str(self.d.items()) )
    def __delitem__(self, index):
        del self.d[ index ]
    def __len__(self):
        return len(self.d)

class BlockStructure (object):
    def __init__(self, block = None):
        self.blocks = IntegerMap()
        self.free_edge_indices = []
        if block:
            self.add_block( block )

    def dump_data(self):
        rv = {}
        blocks = {}
        for index, block in self.blocks.indexed():
            blocks[ index ] = block.dump_data()
        rv["blocks"] = blocks
        rv["connections"] = recursively_untuple( self.extract_connections() )
        return rv

    @staticmethod
    def load_data( data ):
        rv = BlockStructure()
        connections_goal = data["connections"]
        connections_map = {}
        def add_to_map(x,y,x_e,y_e):
            element = y, ((x,x_e), (y,y_e))
            try:
                connections_map[x].append( element )
            except KeyError:
                connections_map[x] = [ element ]
        for [[a,b],[c,d]] in connections_goal:
            add_to_map(a,c,b,d)
            add_to_map(c,a,d,b)
        blocks = {}
        for index, block_data in data["blocks"].items():
            block = Block.load_data( block_data )
            blocks[index] = block
        root_block_index = min( blocks.keys() )
        rv.add_block( blocks[root_block_index], index = root_block_index )
        neighbours = {}
        def add_neighbours_from( x ):
            for neighbour, connection in connections_map[x]:
                neighbours[ neighbour ] = connection
        add_neighbours_from(root_block_index)
        connected_set = set( [root_block_index] )
        while neighbours:
            key = neighbours.keys()[0]
            connection = neighbours[ key ]
            del neighbours[key]
            (x,x_e), (y,y_e) = connection
            if y in connected_set:
                continue
            rv.attach( (x,x_e), blocks[y], y_e, existing_index = y )
            connected_set.add( y )
            add_neighbours_from( y )
        assert recursively_untuple( sorted(connections_goal) ) == recursively_untuple(sorted(rv.extract_connections()))
        return rv

    def area(self):
        return sum( [ block.area() for block in self.blocks ] )

    def translate(self, xy):
        for block in self.blocks:
            block.translate( xy )

    def zero_centroid(self):
        self.translate( -self.centroid() )
        

    def add_block(self, block, index = None):
        if not index:
            index = self.blocks.next_index
        self.free_edge_indices.extend(list(map( lambda edge_index : (index,edge_index), range(len(block.edges)))))
        self.blocks[index] = block

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
        for local_block in self.blocks:
            if local_block.interiors_overlap( block ):
                return True
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

    def attach(self, index, block, block_edge_index, existing_index = None ):
        block_index, edge_index = index
        local_edge = self.edge( index )
        delta_deg = - (180.0 + block.edges[ block_edge_index ].angle_degrees - local_edge.angle_degrees)
#        block = block.clone()
        block.rotate_degrees( delta_deg )
        local_edge = self.edge( index )
        tv = - ( block.edges[ block_edge_index ].a - local_edge.b )
        block.translate( tv )
        local_edge = self.edge( index )
        if self.overlaps( block ):
            raise IllegalOverlapException()
        local_edge = self.edges[ edge_index ]
        foreign_edge = block.edges[ block_edge_index ]
        if not existing_index:
            foreign_block_index = self.blocks.next_index
        else:
            foreign_block_index = existing_index
        self.add_block( block, index = foreign_block_index )
        tbr = []
        for local_block_index, local_edge_index in self.free_edge_indices:
            local_edge = self.edge( (local_block_index,local_edge_index) )
            if local_block_index == foreign_block_index:
                continue
            for foreign_edge_index, foreign_edge in indexed_zip(block.edges):
                if local_edge.overlaps( foreign_edge ):
                    self.blocks[ local_block_index ].free_edge_indices.remove( local_edge_index )
                    self.blocks[ foreign_block_index ].free_edge_indices.remove( foreign_edge_index )
                    block.connections[ foreign_edge_index ] = (local_block_index, local_edge_index)
                    self.blocks[ local_block_index ].connections[ local_edge_index ] = (foreign_block_index, foreign_edge_index)
                    tbr.append( (local_block_index,local_edge_index) )
                    tbr.append( (foreign_block_index,foreign_edge_index) )
        for x in tbr:
            self.free_edge_indices.remove( x )
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
            s.add_sprite( block.create_sprite(), block_pos, rotation = -block.rotation_degrees, key = block )
            for component in block.components:
                try:
                    component.position
                except AttributeError:
                    continue
                if component.required_edges_free():
                    s.add_sprite( component.create_sprite(), block_pos + component.relative_position, rotation = -(block.rotation_degrees + component.relative_angle_degrees), z = -1 )
        return s

def generate_polygon_yaml( filename, n, image_name, side_length = 32.0, colour = (255,255,255), pixel_side_length = None):
    import yaml, sys
    if not pixel_side_length:
        pixel_side_length = side_length
    vertices = generate_regular_polygon_vertices( n, radius_for_side_length( n, side_length ) )
    inner_vertices = generate_regular_polygon_vertices( n, 0.99 * radius_for_side_length( n, side_length ) )
    print >> sys.stderr, "--", filename
    rv = {}
    rv["n"] = n
    rv["hp"] = rv["max-hp"] = 10
    rv["cockpit"] = False
    rv["side-length"] = side_length
    rv["pixel-side-length"] = pixel_side_length
    rv["vertices"] = list([ [x,y] for (x,y) in vertices ])
    rv["inner-vertices"] = list( [ [x,y] for (x,y) in inner_vertices ])
    rv["sprite"] = { "image-name": image_name, "colour": list(colour), "scale": float( side_length ) / float( pixel_side_length ) }
    s = yaml.dump( recursively_untuple(rv) )
    with open( filename, "w" ) as f:
        f.write( s )
    print >> sys.stderr, s

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

if __name__ == '__main__':
    for n in (3,4,5,6,8):
        generate_polygon_yaml( "blocks/poly{}.yaml".format(n), n, "polygon_fancy.{}.generated.png".format(n), pixel_side_length = 76.8 )
