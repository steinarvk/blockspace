from pymunk import Vec2d
import math
import graphics

from util import *

import serialization

class Component (object):
    def __init__(self, block, required_edges = (), name = None):
        self.name = name or "unnamed"
        self.block = block
        self.required_edges = required_edges
        self.block.components.append( self )

    def attach(self, thing):
        pass
        if self.power_production:
            thing.psu.set_production( self, self.power_production )
        if self.power_capacity:
            thing.psu.increase_capacity( self.power_capacity )

    def detach(self, thing):
        pass
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
        return True

    def activated(self, activation_sequence_no = 0):
        pass

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
    def __init__(self, block, position, angle_degrees, **kwargs):
        super( PointComponent, self ).__init__( block, **kwargs )
        self.relative_position = Vec2d(position) # to block
        self.relative_angle_degrees = angle_degrees # relative to block

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

    def create_sheet_info(self, atlas):
        import blocks
        rv = blocks.PolygonBlock.load_file( "blocks/poly8.yaml" ).create_sheet_info( atlas )
        rv[ "colour" ] = 1.0, 1.0, 1.0, 1.0
        rv[ "size" ] = 8.0, 8.0
        return rv

class GeneratorComponent (Component):
    name = "generator"

    def __init__(self, block, production):
        super( GeneratorComponent, self ).__init__( block = block, name = "generator" )
        self.production = production

    def attach(self, thing):
        thing.psu.set_production( self, self.production )

    def detach(self, thing):
        thing.psu.remove_production( self, self.production )

class BatteryComponent (Component):
    name = "battery"

    def __init__(self, block, storage):
        super( BatteryComponent, self ).__init__( block = block, name = "battery" )
        self.storage = storage

    def attach(self, thing):
        thing.psu.increase_capacity( self.storage )

    def detach(self, thing):
        thing.psu.decrease_capacity( self.storage )
    
class GunComponent (PointComponent):
    name = "gun"
    
    def __init__(self, block, position, angle_degrees, cooldown, cost, required_edge):
        super( GunComponent, self ).__init__( block = block, position = position, angle_degrees = angle_degrees, required_edges = (required_edge,), name = "gun" )
        self.cooldown = cooldown
        self.cooldown_finished = None
        self.gun_power_cost = cost
        self.last_usage = (0.0,0)
        self.attached = False

    def may_activate(self):
        if not self.active:
            return False
        if self.cooldown_finished and (self.cooldown_finished > self.world.t):
            return False
        if not self.thing.psu.may_consume( self.gun_power_cost ):
            return False
        return True
        
    def activated(self, activation_sequence_no):
        self.cooldown_finished = self.world.t + self.cooldown
        self.thing.psu.consume( self.gun_power_cost )
        self.last_usage = (self.world.t, activation_sequence_no )

    def attach(self, thing):
        if self.required_edges_free():
            self.thing.weapons.append( self )
            self.attached = True

    def detach(self, thing):
        if self.attached:
            self.thing.weapons.remove( self )

class EngineComponent (PointComponent):
    name = "engine"

    def __init__(self, block, position, angle_degrees, power, cost, required_edge ):
        super( EngineComponent, self ).__init__( block = block, position = position, angle_degrees = angle_degrees, required_edges = (required_edge,), name = "engine" )
        self.engine_power = power
        self.engine_power_cost = cost
        self.attached = False

    def attach(self, thing):
        if self.required_edges_free():
            self.attached = True
            self.thing.engines.append( self )
            thing.thrust_power += self.power_thrusting()
            thing.turn_power += self.power_turning()
            thing.brake_power += self.power_braking()
            thing.engine_power_drain += self.engine_power_cost

    def detach(self, thing):
        if self.attached:
            self.thing.engines.remove( self )
            thing.thrust_power -= self.power_thrusting()
            thing.turn_power -= self.power_turning()
            thing.brake_power -= self.power_braking()
            thing.engine_power_drain -= self.engine_power_cost

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

serialization.register( EngineComponent )
serialization.register( GunComponent )
serialization.register( GeneratorComponent )
serialization.register( BatteryComponent )

def create_component( name, context, **kwargs ):
    return serialization.create_original( name, context, **kwargs )

def is_gun( component ):
    return isinstance( component, GunComponent )

def is_engine( component ):
    return isinstance( component, EngineComponent )

