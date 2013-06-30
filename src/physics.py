import pymunk
import sys

from pymunk import Vec2d
from util import radians_to_degrees, degrees_to_radians

infinite_moment = pymunk.inf

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

class ConvexPolygonShape (CollisionShape):
    def __init__(self, *vertices, **kwargs):
        super( ConvexPolygonShape, self ).__init__( **kwargs )
        self.vertices = vertices
    def generate_basic_shapes(self, body):
        yield pymunk.Poly( body, self.vertices )

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

class CompositeShape (CollisionShape):
    def __init__(self, *shapes, **kwargs ):
        super( CompositeShape, self ).__init__( **kwargs )
        self.shapes = shapes
    def generate_basic_shapes(self, body):
        for shape in self.shapes:
            for rv in shape.generate_shapes( body ):
                yield rv

class DiskShape (CollisionShape):
    def __init__(self, radius, center = (0,0), **kwargs):
        super( DiskShape, self ).__init__( **kwargs )
        self.center = Vec2d( center )
        self.radius = radius
    def generate_basic_shapes(self, body):
        yield pymunk.Circle( body, self.radius, offset = self.center )

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
