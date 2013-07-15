from physics import Vec2d
import math

class Component (object):
    def __init__(self, name, block, required_edges = ()):
        self.name = name
        self.block = block
        self.required_edges = required_edges
        self.block.components.append( self )

    @property
    def active(self):
        xs = self.block.free_edge_indices
        return all( [ (index in xs) for index in self.required_edges ] )

    def __repr__(self):
        return "<Component {1} attached to {0}>".format( repr(self.block), self.name )

class OutOfPower (Exception):
    pass

class PowerSupply (object):
    def __init__(self, max_storage):
        self.max_storage = max_storage
        self.production = {}
        self.consumption = {}
        self.power = 0.0
        self.consumption_fails_hook = lambda x : x.lose_power()
    def set_production(self, key, amount):
        self.production[key] = amount
    def set_consumption(self, key, amount):
        self.consumption[key] = amount
    def remove_production(self, key):
        del self.production[key]
    def remove_consumption(self, key):
        del self.consumption[key]
    def tick(self, dt):
        self.power += sum( self.production.values() ) * dt
        for key, value in self.consumption.items():
            try:
                self.consume( value * dt )
            except OutOfPower:
                self.consumption_fails_hook( key )
        self.power = min( self.power, self.max_storage )
    def charge_rate(self):
        return self.power / self.max_storage
    def consume(self, value):
        if self.power < value:
            raise OutOfPower()
        self.power -= value
    def may_consume(self, value):
        return self.power >= value

class PointComponent (Component):
    def __init__(self, name, block, position, angle_degrees, **kwargs):
        super( PointComponent, self ).__init__( name, block, **kwargs )
        self.relative_position = Vec2d(position) # to block
        self.relative_angle_degrees = angle_degrees # relative to block

    @property
    def position(self):
        return self.block.position + self.relative_position.rotated( self.block.thing.angle_radians ) # correct?

    @property
    def angle_degrees(self):
        return (self.block.angle_degrees + self.relative_angle_degrees) % 360.0

    def __repr__(self):
        return "<PointComponent {3} at {1} {2} attached to {0}>".format( repr(self.block), self.position, self.angle_degrees, self.name )

    @property
    def direction(self):
        return Vec2d(1,0).rotated_degrees( self.angle_degrees )

    @property
    def velocity(self):
        rel = self.block.translation + self.relative_position
        r = rel.length
        b = rel.rotated_degrees( self.block.thing.angle_degrees + 90.0 ).normalized()
        rv = b * (self.block.thing.angular_velocity_radians * r)
        lv = self.block.thing.velocity
        return lv + rv


