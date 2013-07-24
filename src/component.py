from pymunk import Vec2d
import math
import graphics

from util import *

class Component (object):
    def __init__(self, block, required_edges = (), categories = (), category = None, name = None):
        self.name = name or "unnamed"
        self.block = block
        self.required_edges = required_edges
        self.block.components.append( self )
        self.cooldown = None
        self.cooldown_finished = 0.0
        self.power_usage = None
        self.last_usage = None
        self.categories = list(categories)
        self.power_production = None
        self.power_capacity = None
        if category:
            self.categories.append( category )

    def attach(self, thing):
        print "current capacity", thing.psu.max_storage
        if self.power_production:
            thing.psu.set_production( self, self.power_production )
        if self.power_capacity:
            thing.psu.increase_capacity( self.power_capacity )
        print "attached", self.thing.psu.max_storage

    def detach(self, thing):
        if self.power_production:
            thing.psu.remove_production( self )
        if self.power_capacity:
            thing.psu.decrease_capacity( self.power_capacity )

    @property
    def world(self):
        return self.thing.world

    @property
    def thing(self):
        return self.block.thing

    def may_activate(self):
        if not self.active:
            return False
        if self.cooldown and self.cooldown_finished and (self.cooldown_finished > self.world.t):
            return False
        if self.power_usage and not self.thing.psu.may_consume( self.power_usage ):
            return False
        return True

    def activated(self, activation_sequence_no = 0):
        if self.cooldown:
            self.cooldown_finished = self.world.t + self.cooldown
        if self.power_usage:
            self.thing.psu.consume( self.power_usage )
        self.last_usage = (self.world.t, activation_sequence_no )

    def required_edges_free(self):
        xs = self.block.free_edge_indices
        return all( [ (index in xs) for index in self.required_edges ] )

    @property
    def active(self):
        return self.required_edges_free()

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
    def increase_capacity(self, amount):
        self.max_storage += amount
    def decrease_capacity(self, amount):
        self.max_storage -= amount
        self.power = max(0, min( self.max_storage, self.power ) )
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
        if self.max_storage == 0:
            return 0.0
        return self.power / self.max_storage
    def consume(self, value):
        if self.power < value:
            raise OutOfPower()
        self.power -= value
    def may_consume(self, value):
        return self.power >= value

class PointComponent (Component):
    def __init__(self, block, position, angle_degrees, sprite_info = None, **kwargs):
        super( PointComponent, self ).__init__( block, **kwargs )
        self.relative_position = Vec2d(position) # to block
        self.relative_angle_degrees = angle_degrees # relative to block
        self.sprite_info = sprite_info

    def create_sprite(self):
        return graphics.create_sprite( self.sprite_info )

    @property
    def angle_from_thing_degrees(self):
        return degrees_sub( self.angle_degrees, self.thing.angle_degrees )

    @property
    def position(self):
        return self.block.position + self.relative_position.rotated_degrees( self.block.angle_degrees )

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

class EngineComponent (PointComponent):
    def __init__(self, engine_power, *args, **kwargs ):
        super( EngineComponent, self ).__init__( *args, **kwargs )
        self.engine_power = engine_power

    def efficiency_at_angle( self, deg ):
        deg_from_ideal = degrees_sub( self.angle_from_thing_degrees, deg + 180 )
        x = math.cos( degrees_to_radians( deg_from_ideal ) )
        return 0.1 + 0.9 * 0.5 * (1+x)

    def efficiency_forwards( self ):
        return self.efficiency_at_angle(0)

    def efficiency_backwards( self ):
        return self.efficiency_at_angle( 180 )

    def efficiency_sideways( self ):
        return max( self.efficiency_at_angle( 90 ), self.efficiency_at_angle( 270 ) )

    def power_thrusting(self):
        return self.efficiency_forwards() * self.engine_power

    def power_turning(self):
        return self.efficiency_sideways() * self.engine_power

    def power_braking(self):
        return self.efficiency_backwards() * self.engine_power
