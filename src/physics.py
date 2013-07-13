import pymunk
import sys
import math
import random

from pymunk import Vec2d
from util import radians_to_degrees, degrees_to_radians

infinity = infinite_moment = pymunk.inf

def zero_shape_centroid( shape ):
    shape.translate( shape.centroid() * -1 )
    return shape

def calculate_maximum_timestep( minimum_diameter, maximum_speed ):
    return (0.5 * minimum_diameter) / maximum_speed

def calculate_minimum_diameter( timestep, maximum_speed ):
    return timestep * maximum_speed * 2

def calculate_maximum_speed( timestep, minimum_diameter ):
    return (0.5 * minimum_diameter) / timestep

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

class CollisionShape (object):
    def __init__(self, group = None, sensor = None, collision_type = None, elasticity = None, extra_info = None, origin = None):
        self.group = group
        self.sensor = sensor
        self.collision_type = collision_type
        self.elasticity = elasticity
        self.extra_info = extra_info
        self.origin = origin
    def decorate_shape(self, shape):
        if self.group != None:
            shape.group = self.group
        if self.sensor != None:
            shape.sensor = self.sensor
        if self.collision_type != None:
            shape.collision_type = self.collision_type
        if self.elasticity != None:
            shape.elasticity = self.elasticity
        if self.extra_info != None:
            shape.extra_info = self.extra_info
        if self.origin:
            self.origin.register_shape( shape )
        return shape
    def generate_shapes(self, body):
        for shape in self.generate_basic_shapes( body ):
            yield self.decorate_shape( shape )
    def centroid_and_area(self):
        return self.centroid(), self.area()

class ConvexPolygonShape (CollisionShape):
    def __init__(self, *vertices, **kwargs):
        super( ConvexPolygonShape, self ).__init__( **kwargs )
        self.vertices = map( Vec2d, vertices )
    def generate_basic_shapes(self, body):
        yield pymunk.Poly( body, self.vertices )
    def area(self):
        rv = 0.0
        for (xi,yi), (xip,yip) in closed_circle_pairs( self.vertices ):
            rv += xi * yip - yi * xip
        return 0.5 * rv
    def centroid_and_area(self):
        a = 0.0
        rvx, rvy = 0.0, 0.0
        for (xi,yi), (xip,yip) in closed_circle_pairs( self.vertices ):
            a += xi * yip - yi * xip
            rvx += (xi + xip) * (xi * yip - xip * yi)
            rvy += (yi + yip) * (xi * yip - xip * yi)
        signed_area = 0.5 * a
        return (Vec2d(rvx,rvy) / (6.0 * signed_area)), abs(signed_area)
    def centroid(self):
        return self.centroid_and_area()[0]
    def triangulate(self):
        a = self.vertices[0]
        for b, c in successive_pairs( self.vertices[1:] ):
            yield (a,b,c)
    def translate(self, xy):
        self.vertices = [ v + xy for v in self.vertices ]

def generate_random_scalar():
    return (random.random() - 0.5) * 100

def generate_random_point():
    return generate_random_scalar(), generate_random_scalar()

def generate_random_convex_polygon_shape():
    n = random.randint(4, 10)
    r = random.random() * 10
    x, y = generate_random_point()
    angles = [ math.pi * 2 * i / float(n) for i in range(n) ]
    return ConvexPolygonShape(*[(x+r*math.cos(a), y + r*math.sin(a)) for a in angles])

def generate_random_disk_shape():
    r = random.random() * 10.0
    return DiskShape( r, generate_random_point() )

def generate_random_triangle_shape():
    angles = [ random.random(), random.random(), random.random() ]
    r = random.random() * 10
    angles.sort()
    angles = [ a * math.pi * 2 for a in angles ]
    return TriangleShape(*[(x+r*math.cos(a), y + r*math.sin(a)) for a in angles])

class TriangleShape (ConvexPolygonShape):
    def __init__(self, a, b, c, **kwargs):
        super( TriangleShape, self ).__init__( a, b, c, **kwargs)

class SegmentShape (CollisionShape):
    def __init__(self, a, b, radius = 0.001, **kwargs):
        super( SegmentShape, self ).__init__( **kwargs )
        self.a = Vec2d(a)
        self.b = Vec2d(b)
        self.radius = radius
    def generate_basic_shapes(self, body):
        yield pymunk.Segment( body, self.a, self.b, radius = self.radius )
    def area(self):
        return 0.0
    def centroid(self):
        return (a+b) * 0.5
    def triangulate(self):
        return []
    def translate(self, xy):
        self.a = self.a + xy
        self.b = self.b + xy

class CompositeShape (CollisionShape):
    def __init__(self, *shapes, **kwargs ):
        super( CompositeShape, self ).__init__( **kwargs )
        self.shapes = shapes
    def generate_basic_shapes(self, body):
        for shape in self.shapes:
            for rv in shape.generate_shapes( body ):
                yield rv
    def area(self):
        return sum(map( lambda x : x.area(), self.shapes ))
    def centroid(self):
        rv = Vec2d(0,0)
        total_area = 0.0
        for centroid, area in map( lambda x : x.centroid_and_area(), self.shapes):
            rv += centroid * area
            total_area += area
        rv /= total_area
        return rv
    def triangulate(self):
        for shape in self.shapes:
            for abc in shape.triangulate():
                yield abc
    def translate(self, xy):
        for shape in self.shapes:
            shape.translate( xy )
        

class DiskShape (CollisionShape):
    def __init__(self, radius, center = (0,0), **kwargs):
        super( DiskShape, self ).__init__( **kwargs )
        self.center = Vec2d( center )
        self.radius = radius
    def generate_basic_shapes(self, body):
        yield pymunk.Circle( body, self.radius, offset = self.center )
    def area(self):
        return math.pi * self.radius * self.radius
    def centroid(self):
        return self.center
    def triangulate(self):
        n = 100
        for i in range(n):
            a0 = math.pi * 2.0 * i / float(n)
            a1 = math.pi * 2.0 * (i+1) / float(n)
            b = self.radius * math.cos(a0), self.radius * math.sin(a0)
            c = self.radius * math.cos(a1), self.radius * math.sin(a1)
            yield (self.center,b,c)
    def translate(self, xy):
        self.center = self.center + xy

class PhysicsSimulator (object):
    def __init__(self, timestep = 0.001, speed_limit = 2000.0, size_limit = 5.0):
        self.space = pymunk.Space()
        self._t = 0.0
        self._timestep = timestep
        self._next_group = 1
        if self._timestep:
            if speed_limit == None:
                speed_limit = calculate_maximum_speed( self._timestep, size_limit )
            if size_limit == None:
                size_limit = calculate_minimum_diameter( self._timestep, speed_limit )
        self.speed_limit = speed_limit
        self.object_size_lower_limit = size_limit
        if self._timestep:
            assert calculate_maximum_timestep( self.object_size_lower_limit, self.speed_limit ) >= self._timestep
        self.marked_for_removal = []
        self.marked_for_addition = []
    def remove(self, *args):
        self.marked_for_removal.extend( args )
    def add(self, *args):
        self.marked_for_addition.extend( args )
    def perform_removals(self):
        if self.marked_for_removal:
            self.space.remove( *set(self.marked_for_removal) )
            self.marked_for_removal = []
    def perform_additions(self):
        if self.marked_for_addition:
            self.space.add( *set(self.marked_for_addition) )
            self.marked_for_addition = []
    def tick(self, dt):
        if self._timestep:
            self._t += dt
            while self._t >= self._timestep:
                self.space.step( self._timestep )
                self._t -= self._timestep
        else:
            self.space.step( dt )
    def new_group_id(self):
        rv = self._next_group
        self._next_group += 1
        return rv

class StaticObstacle (object):
    def __init__(self, sim, shape, name = "obstacle"):
        self.name = name
        self.body = pymunk.Body()
        self.shapes = list( shape.generate_shapes( self.body ) )
        for shape in self.shapes:
            shape.thing = self
        sim.space.add( *self.shapes )

class Thing (object):
    def __init__(self, world, shape, mass, moment, group = False, name = "anonymous", collision_type = None ):
        self.world = world
        self.sim = self.world.sim
        self.name = name
        self.body = pymunk.Body( mass, moment )
        self.body.velocity_limit = self.sim.speed_limit
        self.shapes = []
        self.invulnerable = True
        self.group = group
        self.collision_type = collision_type
        self.reshape( shape )
        for shape in self.shapes:
            bb = shape.cache_bb()
            assert min( abs(bb.right-bb.left), abs(bb.top-bb.bottom) ) >= self.sim.object_size_lower_limit
            shape.thing = self
        self.kill_hooks = []
        self.update_hooks = []
        self.alive = True
        self.killed = False
        self.sim.space.add( self.body )

    def reshape(self, shape):
        if self.shapes:
            self.sim.remove( *self.shapes )
        self.abstract_shape = shape
        self.centroid = shape.centroid()
        self.shapes = list( shape.generate_shapes( self.body ) )
        for shape in self.shapes:
            bb = shape.cache_bb()
            assert min( abs(bb.right-bb.left), abs(bb.top-bb.bottom) ) >= self.sim.object_size_lower_limit
            shape.thing = self
        if self.collision_type:
            for shape in self.shapes:
                shape.collision_type = self.collision_type
        if self.group:
            for shape in self.shapes:
                shape.group = self.group
        self.sim.add( *self.shapes )

    def update(self):
        for hook in self.update_hooks:
            hook( self )

    def kill(self):
        if self.killed:
            return
        self.killed = True
        self.sim.remove( self.body, *self.shapes )
        self.alive = False
        self.world.remove_all_hooks( self )
        for hook in self.kill_hooks:
            hook( self )

    @property
    def position(self):
        return Vec2d(self.body.position)

    @position.setter
    def position(self, value):
        self.body.position = value

    @property
    def velocity(self):
        return Vec2d(self.body.velocity)

    @velocity.setter
    def velocity(self, value):
        self.body.velocity = value

    @property
    def speed(self):
        return self.body.velocity.get_length()

    @property
    def angular_velocity_radians(self):
        return self.body.angular_velocity

    @angular_velocity_radians.setter
    def angular_velocity_radians(self, value):
        self.body.angular_velocity = value

    @property
    def angular_velocity_degrees(self):
        return radians_to_degrees( self.body.angular_velocity )

    @angular_velocity_degrees.setter
    def angular_velocity_degrees(self, value):
        self.body.angular_velocity = degrees_to_radians( value )

    @property
    def angle_radians(self):
        return self.body.angle

    @angle_radians.setter
    def angle_radians(self, value):
        self.body.angle = value

    @property
    def angle_degrees(self):
        return radians_to_degrees( self.body.angle )

    @angle_degrees.setter
    def angle_degrees(self, value):
        self.body.angle = degrees_to_radians( value )

    @angle_degrees.setter
    def angle_degrees(self, value):
        self.body.angle = degrees_to_radians( value )

    @property
    def direction(self):
        return Vec2d(1,0).rotated( self.body.angle )

def calculate_velocities( wpv ):
    total_force = Vec2d(0,0)
    total_weight = 0.0
    total_rot = 0.0
    for weight, position, force in wpv:
        position = Vec2d(position)
        force = Vec2d(force)
        total_weight += weight
        total_force += force * weight
        r = position.get_length()
        if r > 0.0:
            rot = force * 180.0 / (2 * math.pi * r)
            total_rot += rot * weight
    return total_force / total_weight, total_rot / total_weight
