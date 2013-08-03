import graphics
import physics
import gameinput

from physics import ConvexPolygonShape, DiskShape, Vec2d
from gameinput import key

import cocos

import random

from util import *

from pyglet.gl import *

from functools import partial
from itertools import cycle

import pygame
from pymunk.pygame_util import draw_space
import pymunk

import blocks
import component

from blocks import BlockStructure

from component import create_component

from operator import attrgetter

class Ship (physics.Thing):
    def __init__(self, world, block_structure, position, mass = None, moment = None, layer = None, cocos_parent = None, **kwargs):
        density = 1/(32.*32.)
        if not mass:
            mass = block_structure.area() * density
        if not moment:
            moment = 0
            for block in block_structure.blocks:
                block_mass = block.area() * density
                moment += pymunk.moment_for_poly( block_mass, block.transformed_vertices(), (0,0) )
        super( Ship, self ).__init__( world, block_structure.create_collision_shape(), mass, moment, collision_type = physics.CollisionTypes["main"], **kwargs )
        self.block_structure = block_structure
        self.layer = layer
        self.world.pre_display.add_hook( self, self.update_graphics )
        self.sprite = self.main_sprite_structure = self.block_structure.create_sys_structure( world.object_psys, world.atlas, self )
        def recreate_sprite_structure():
            self.main_sprite_structure.kill()
            self.sprite = self.main_sprite_structure = self.block_structure.create_sys_structure( world.object_psys, world.atlas, self )
        def kill_sprite_structure():
            self.main_sprite_structure.kill()
        self.kill_hooks.append( ignore_arguments( kill_sprite_structure ) )
        self.reshape_hooks.add_anonymous_hook( recreate_sprite_structure )
        self.body.velocity_limit = min( self.body.velocity_limit, 700.0 )
        self.body.angular_velocity_limit = degrees_to_radians( 360.0 )
        self.position = position
        self._spin = 0
        self._thrusting = False
        self._braking = False
        self._turbo_multiplier = 2
        self._ai_time = 0.0
        self._shooting = False
        self.minimap_symbol_sprite = None
#        f = self.sprite.cocos_sprite.draw
#        self.sprite.cocos_sprite.draw = lambda : (f(), graphics.draw_thing_shapes(self))
        self.psu.consumption_fails_hook = lambda key : self.lose_power( key )
        self.reattach_components()
        self.psu.power = self.psu.max_storage

    def reattach_components(self):
        power = self.psu.power
        self.psu = component.PowerSupply(0.0)
        self.weapons = []
        self.engines = []
        self.thrust_power = 0
        self.brake_power = 0
        self.turn_power = 0
        self.engine_power_drain = 0
        for block in self.block_structure.blocks:
            block.attach_components( self )
        self.psu.power = min( self.psu.max_storage, power )

    @staticmethod
    def load_data(data, world, **kwargs):
        s = BlockStructure.load_data( data["block-structure"] )
        s.zero_centroid()
        mass = data["mass"]
        moment = data["moment"]
        rv = Ship( world, s, (0,0), mass = mass, moment = moment, **kwargs )
        return rv

    def summarize(self):
        return "Ship at {pos} with {power}/{maxpower} power movement {thrust}/{turn}/{brake} ({drain})".format( pos = self.position, power = self.psu.power, maxpower = self.psu.max_storage, thrust = self.thrust_power, turn = self.turn_power, brake = self.brake_power, drain = self.engine_power_drain )

    @staticmethod
    def load_string( s, *args, **kwargs ):
        import yaml
        return Ship.load_data( yaml.safe_load( s ), *args, **kwargs )

    @staticmethod
    def load_file( fn, *args, **kwargs ):
        with open( fn, "r" ) as f:
            return Ship.load_string( f.read(), *args, **kwargs )
        
    def dump_data(self):
        rv = {}
        rv[ "block-structure" ] = self.block_structure.dump_data()
        rv[ "mass" ] = self.mass
        rv[ "moment" ] = self.moment
        return rv

    def dump_string(self):
        import yaml
        return yaml.dump( self.dump_data() )

    def dump_file( self, fn ):
        with open( fn, "w" ) as f:
            f.write( self.dump_string() )

    def lose_power(self, key):
        if key == "engine":
            self._thrusting = False
        elif key == "brakes":
            self._braking  = False
        elif key == "turning":
            self._spin = 0
        elif key == "turbo":
            self._turbo = False
        else:
            print "lost unknown power", key
    def on_fire_key(self, symbol, modifiers, state):
        pass
    def sanity_check(self):
        pass
    def on_controls_state(self, symbol, modifiers, state):
        self.sanity_check()
        self._spin = (1 if state[key.RIGHT] else 0) - (1 if state[key.LEFT] else 0)
        self._thrusting = state[key.UP]
        self._braking = state[key.DOWN]
        self._turbo = state[key.LSHIFT]
        self._shooting = state[key.SPACE]
        self.psu.set_consumption( "engine", self.engine_power_drain if self._thrusting else 0 )
        self.psu.set_consumption( "brakes", self.engine_power_drain if self._braking else 0 )
        self.psu.set_consumption( "turning", self.engine_power_drain if self._spin != 0 else 0 )
        self.psu.set_consumption( "turbo", self.engine_power_drain if self._turbo and self._thrusting else 0 )
    def all_engines(self):
        rv = [ engine for engine in self.engines if engine.active ]
        return rv
    def all_guns(self):
        rv = [ gun for gun in self.weapons if gun.active ]
        rv.sort( key = lambda x : x.last_usage )
        return rv
    def ready_guns(self):
        rv = [ gun for gun in self.weapons if gun.may_activate() ]
        rv.sort( key = lambda x : x.last_usage )
        return rv
    def may_fire(self):
        return bool( self.ready_guns() )
    def update_graphics(self):
        self.main_sprite_structure.update_elements()
    def update(self, dt):
        super( Ship, self ).update()
        if self.minimap_symbol_sprite:
            self.minimap_symbol_sprite.position = self.position
        if self._shooting:
            self.world.shoot_volley( self )
        self.body.reset_forces()
        spin = self._spin
        rotation_distance = 100
        rotation_force_size = self.turn_power
        if spin == 0:
            delta_angular_momentum = rotation_force_size * rotation_distance * dt
            angular_momentum = self.body.angular_velocity * self.body.moment
            if angular_momentum > 0 and abs(angular_momentum) > delta_angular_momentum:
                spin = 1
            elif angular_momentum < 0 and abs(angular_momentum) > delta_angular_momentum:
                spin = -1
            else:
                self.body.angular_velocity = 0
        rotation_force = Vec2d(self.turn_power,0) * spin
        rotation_offset = Vec2d(0,rotation_distance)
        self.body.apply_force( rotation_force, rotation_offset )
        self.body.apply_force( -rotation_force, -rotation_offset )
        forces = []
        if self._thrusting:
            force = (self._turbo_multiplier if self._turbo else 1) * self.thrust_power
            dx, dy = polar_degrees( self.angle_degrees, force )
            forces.append( Vec2d( dx, dy ) )
        if self._braking:
            stopforce = self.body.velocity.normalized() * -1 * self.brake_power
            if self.velocity.get_length() < stopforce.get_length() * 0.01:
                forces = []
                self.body.velocity = Vec2d(0,0)
            else:
                forces.append( stopforce )
        self.body.apply_force( reduce( lambda x,y: x+y, forces, Vec2d(0,0) ) )
    def destroy_block(self, block_index):
        block = self.block_structure.blocks[ block_index ]
        index = block_index
        detached_block = self.block_structure.remove_block( index )
        detachable_blocks = []
        detached_parts = []
        if index == 0:
            survivor = None
            for index, block in self.block_structure.blocks.indexed():
                    if index != 0:
                        detachable_blocks.append( index )
        else:
            survivor = self.block_structure.any_block_index()
            if survivor != None:
                survivors = self.block_structure.connectivity_set_of( survivor )
                for index, block in self.block_structure.blocks.indexed():
                    if index not in survivors:
                        detachable_blocks.append( index )
        while detachable_blocks:
            x = self.block_structure.connectivity_set_of( detachable_blocks.pop(0) )
            detached_parts.append( x )
            detachable_blocks = filter( lambda z : z not in x, detachable_blocks )
        def on_detached_single_block( detached_block ):
            vel = detached_block.velocity
            deg = detached_block.angle_degrees
            pos = detached_block.position
            r, g, b = detached_block.colour
            tr,tg,tb = 0.5,0.5,0.75
            detached_block.colour = int(r*tr),int(g*tg),int(b*tb)
            def create_later():
                debris = create_ship_thing( self.world, pos, shape = blocks.BlockStructure( detached_block ), recolour = False )
                debris.angle_degrees = deg
                debris.velocity = vel
            self.world.queue_once( create_later )
        on_detached_single_block( detached_block )
        for detached_part in detached_parts:
            # this must be amended to reconstruct the connections
            for index in detached_part:
                db = self.block_structure.remove_block( index )
                on_detached_single_block( db )
        if survivor != None:
            remaining_block = self.block_structure.blocks[survivor]
            wpv = [(1,b.position-self.position,b.velocity) for b in self.block_structure.blocks ]
            pos_before = remaining_block.position
            angle_before = remaining_block.angle_degrees
            self.block_structure.zero_centroid()
            self.block_structure.clear_collision_shape()
            self.reshape( self.block_structure.create_collision_shape() )
            pos_after = remaining_block.position
            angle_after = remaining_block.angle_degrees
            self.position -= (pos_after - pos_before)
            linear, rotational = physics.calculate_velocities( wpv )
            self.velocity = linear
            self.angular_velocity = rotational
            pos_after = remaining_block.position
            angle_after = remaining_block.angle_degrees
            assert degrees_almost_equal( angle_after, angle_before )
            assert vectors_almost_equal( pos_before, pos_after )
        density = 1/1024.
        area = self.block_structure.area()
        mass = density * area
        self.reattach_components()
        if mass > 0:
            self.mass = mass
        if len(self.block_structure.blocks) == 0:
            self.kill()

class Debris (physics.Thing):
    def __init__(self, world, layer, position, shape, sprite, mass = 1.0, moment = 1.0, **kwargs):
        super( Debris, self ).__init__( world, shape, mass, moment, **kwargs )
        if sprite:
            graphics.Sprite( sprite, self, layer )
            self.sprite.cocos_sprite.draw = lambda : graphics.draw_thing_shapes(self)
        self.position = position
#        f = self.sprite.cocos_sprite.draw
#        self.sprite.cocos_sprite.draw = lambda : (f(), graphics.draw_thing_shapes(self))
    def update(self):
        super( Debris, self ).update()

def with_engine( block, edge_index = 3 ):
    try:
        rv = block
        for index in edge_index:
            rv = with_engine( rv, index )
        return rv
    except TypeError:
        pass
    angle = block.edge( edge_index ).angle_degrees
    pos = Vec2d( polar_degrees( angle, 16.0 ) )
    pos = Vec2d(0,0)
    pos = block.edge( edge_index ).midpoint()
    context = { "block": block }
    engine = create_component( "engine", context, position = pos, angle_degrees = angle, required_edge = edge_index, power = 500, cost = 50 )
    return block

def with_gun( block, edge_index = 1 ):
    try:
        rv = block
        for index in edge_index:
            rv = with_gun( rv, index )
        return rv
    except TypeError:
        pass
    angle = block.edge( edge_index ).angle_degrees
    pos = Vec2d( polar_degrees( angle, 16.0 ) )
    pos = Vec2d(0,0)
    pos = block.edge( edge_index ).midpoint()
    context = { "block": block }
    cooldown = 0.2
#   .cooldown = 0.1 # a LOT more powerful with lower cooldown
    cost = (750 * cooldown) * 2.0/3.0 # more reasonable power usage
    gun = create_component( "gun", context, position = pos, angle_degrees = angle, required_edge = edge_index, cooldown = cooldown, cost = cost)
    return block

def with_guns( block, sprite = None ):
    return with_gun( block, range(len(block.edges)) )
        

def create_ship_thing(world, position, shape = "small", hp = 1, recolour = True):
    def w_engine( b, edge_index = 2):
        return with_engine( b, edge_index = edge_index )
    def w_cockpit( b ):
        return b
    def w_gun( b, edge_index = 0 ):
        return with_gun( b, edge_index = edge_index )
    def w_guns( b ):
        return with_guns( b )
    def quad_block():
        return blocks.PolygonBlock.load_file( "blocks/poly4.yaml" )
    def octa_block():
        return blocks.PolygonBlock.load_file( "blocks/poly8.yaml" )
    # default orientation changed:
    #  1
    # 2 0
    #  3
    if shape == "small":
        s = blocks.BlockStructure( w_engine(w_gun(w_cockpit(quad_block()))) )
        s.attach((0,3), w_engine(w_gun(quad_block())), 1)
        s.attach((0,0), w_engine(w_gun(quad_block())), 2)
        s.attach((0,1), w_engine(w_gun(quad_block(), (0,1,2,3) )), 3)
    elif shape == "big":
        s = blocks.BlockStructure( w_engine(w_cockpit(quad_block())) )
        s.attach((0,2), w_engine(quad_block()), 0)
        s.attach((0,0), w_engine(quad_block()), 2)
        s.attach((0,1), w_engine(quad_block()), 3)
        s.attach((3,2), w_engine(quad_block()), 0)
        s.attach((3,0), w_engine(quad_block()), 2)
        s.attach((3,1), w_engine(w_gun(quad_block(), 1)), 3)
    elif shape == "bigger":
        s = blocks.BlockStructure( w_gun(w_engine(quad_block())) )
        s.attach((0,2), w_gun(w_engine(quad_block())), 0)
        s.attach((0,0), w_gun(w_engine(quad_block())), 2)
        s.attach((0,1), w_gun(w_engine(quad_block())), 3)
        s.attach((3,2), w_gun(w_engine(quad_block())), 0)
        s.attach((3,0), w_gun(w_engine(quad_block())), 2)
        s.attach((3,1), w_gun(w_engine(quad_block())), 3)
        s.attach((6,2), w_gun(w_engine(quad_block())), 0)
        s.attach((6,0), w_gun(w_engine(quad_block())), 2)
        s.attach((6,1), w_gun(w_engine(quad_block())), 3)
    elif shape == "single_weird":
        s = blocks.BlockStructure( w_gun(w_engine(blocks.PolygonBlock.load_file( "blocks/poly5.yaml" ) ) ) )
    elif shape == "single":
        s = blocks.BlockStructure( w_guns( w_cockpit( quad_block() ) ) )
    elif shape == "octa":
        s = blocks.BlockStructure( w_guns( w_cockpit( octa_block() ) ) )
        for i in range(7):
            a = s.attach((0,i), quad_block(), 0)
            b = s.attach((a,2), quad_block(), 0)
            c = s.attach((b,2), quad_block(), 0)
            d = s.attach((c,1), w_gun(quad_block(), 1), 3)
    elif shape == "wide":
        s = blocks.BlockStructure( w_guns(w_engine( quad_block() )) )
        s.attach((0,1), w_engine(w_guns(quad_block())), 3)
        l, r = 0, 0
        for i in range(6):
            l = s.attach((l,2), w_guns(w_engine(quad_block())), 0)
            r = s.attach((r,0), w_guns(w_engine(quad_block())), 2)
        l = s.attach((l,2), w_guns(w_engine(quad_block())), 0)
        r = s.attach((r,0), w_guns(w_engine(quad_block())), 2)
    elif shape == "long":
        s = blocks.BlockStructure( w_cockpit( quad_block() ) )
        l, r = 0, 0
        for i in range(6):
            l = s.attach((l,3), w_guns(quad_block()), 1)
            r = s.attach((r,1), w_guns(quad_block()), 3)
    else:
        s = shape
    s.zero_centroid()
    if recolour:
        colours = { "blue": (0,0,255),
                    "purple": (255,0,255),
                    "white": (255,255,255),
                    "green": (0,255,0),
                    "yellow": (255,255,0),
                    "dark-gray": (64,64,64),
                    "red": (255,0,0) }
        def make_cockpit( block ):
            context = { "block": block }
            create_component( "generator", context, production = int(0.5 + 0.5 * block.area()) )
            create_component( "battery", context, storage = int(0.5 + 0.5 * block.area()) )
            block.max_hp = block.hp = hp * 3
            block.colour = colours["green"]
            block.cockpit = True
        def make_battery( block ):
            context = { "block": block }
            create_component( "battery", context, storage = block.area() )
            block.colour = colours["yellow"]
        def make_generator( block ):
            context = { "block": block }
            create_component( "generator", context, production = int(0.5 + 0.5 * block.area()) )
            block.colour = colours["red"]
        def make_armour( block ):
            block.max_hp = block.hp = hp * 3
            block.colour = colours["dark-gray"]
        gens = make_battery, make_generator, make_armour
        gens = (make_armour,)
        for block in s.blocks:
            block.max_hp = block.hp = hp
            block.cockpit = False
        for block in list(s.blocks)[1:]:
            random.choice(gens)( block )
        make_cockpit( s.blocks[0] )
    rv = Ship( world, s, position, mass = len(s.blocks), moment = 20000.0 )
    rv._gun_distance = 65
    return rv

