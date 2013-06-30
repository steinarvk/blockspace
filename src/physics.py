import pymunk
import sys
import math

from pymunk import Vec2d
from util import radians_to_degrees, degrees_to_radians

infinite_moment = pymunk.inf

def closed_circle( l ):
    it = l.__iter__()
    first_element = it.next()
    yield first_element
    for element in it:
        yield element
    yield first_element

def successive_pairs( l ):
    it = l.__iter__()
    a = it.next()
    b = it.next()
    while True:
        yield (a,b)
        a = b
        b = it.next()

def closed_circle_pairs( l ):
    return successive_pairs( closed_circle( l ) )

class CollisionShape (object):
    def __init__(self, group = None, sensor = None, collision_type = None, elasticity = None):
        self.group = group
        self.sensor = sensor
        self.collision_type = collision_type
        self.elasticity = elasticity
    def decorate_shape(self, shape):
        if self.group != None:
            shape.group = self.group
        if self.sensor != None:
            shape.sensor = self.sensor
        if self.collision_type != None:
            shape.collision_type = self.collision_type
        if self.elasticity != None:
            shape.elasticity = self.elasticity
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

class PhysicsSimulator (object):
    def __init__(self, timestep = 0.001):
        self.space = pymunk.Space()
        self._t = 0.0
        self._timestep = timestep
        self._next_group = 1
        self.speed_limit = 2000.0
        self.object_size_lower_limit = 5.0
    def tick(self, dt):
        self._t += dt
        while self._t >= self._timestep:
            self.space.step( self._timestep )
            self._t -= self._timestep
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
    def __init__(self, sim, shape, mass, moment, group = False, name = "anonymous" ):
        self.name = name
        self.body = pymunk.Body( mass, moment )
        self.body.velocity_limit = sim.speed_limit
        self.shapes = list( shape.generate_shapes( self.body ) )
        if group and len(self.shapes) > 1:
            groupno = sim.new_group_id()
            for shape in self.shapes:
                shape.group = groupno
        for shape in self.shapes:
            bb = shape.cache_bb()
            assert min( abs(bb.right-bb.left), abs(bb.top-bb.bottom) ) >= sim.object_size_lower_limit
            shape.thing = self
        sim.space.add( self.body, *self.shapes )

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
    def angle_radians(self):
        return self.body.angle

    @property
    def angle_degrees(self):
        return radians_to_degrees( self.body.angle )
