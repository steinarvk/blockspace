import pymunk

from pymunk import Vec2d

infinite_moment = pymunk.inf

class CollisionShape (object):
    def __init__(self, group = None, sensor = None, collision_type = None):
        self.group = group
        self.sensor = sensor
        self.collision_type = collision_type
    def decorate_shape(self, shape):
        if self.group != None:
            shape.group = self.group
        if self.sensor != None:
            shape.sensor = self.sensor
        if self.collision_type != None:
            shape.collision_type = self.collision_type
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

class DiskShape (object):
    def __init__(self, radius, center = (0,0)):
        self.center = Vec2d( center )
        self.radius = radius
    def generate_basic_shapes(self, body):
        yield pymunk.Circle( body, radius, offset = self.center )

class PhysicsSimulator (object):
    def __init__(self, timestep = 0.001):
        self.space = pymunk.Space()
        self.t = 0.0
        self.timestep = timestep
    def tick(self, dt):
        self.t += dt
        while self.t > self.timestep:
            self.space.step( self.timestep )
            self.t -= self.timestep

class Thing (object):
    def __init__(self, mass, moment = None):
        pass
