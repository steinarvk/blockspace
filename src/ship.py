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

from operator import attrgetter

class Ship (physics.Thing):
    def __init__(self, world, block_structure, position, mass = 1.0, moment = 1.0, layer = None, cocos_parent = None, **kwargs):
        super( Ship, self ).__init__( world, block_structure.create_collision_shape(), mass, moment, **kwargs )
        self.block_structure = block_structure
        self.layer = layer
        self.cocos_parent = cocos_parent
        self.sprite = self.main_sprite_structure = self.block_structure.create_sprite_structure( layer = self.layer, cocos_parent = self.cocos_parent, thing = self )
        def recreate_sprite_structure():
            self.main_sprite_structure.kill()
            self.sprite = self.main_sprite_structure = self.block_structure.create_sprite_structure( layer = self.layer, cocos_parent = self.cocos_parent, thing = self )
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
        for block in self.block_structure.blocks:
            block.attach_components( self )
        self.refresh_engines()
                
        self.psu.power = self.psu.max_storage

    def refresh_engines(self):
        self.thrust_power = 0
        self.brake_power = 0
        self.turn_power = 0
        self.engine_power_drain = 0
        for engine in self.block_structure.get_components( lambda c : "engine" in c.categories and c.active ):
            self.thrust_power += engine.power_thrusting()
            self.turn_power += engine.power_turning()
            self.brake_power += engine.power_braking()
            self.engine_power_drain += engine.power_usage

    @property
    def mass(self):
        return self.body.mass

    @property
    def moment(self):
        return self.body.moment

    @staticmethod
    def load_data(data, world, **kwargs):
        s = BlockStructure.load_data( data["block-structure"] )
        mass = data["mass"]
        moment = data["moment"]
        rv = Ship( world, s, (0,0), mass = mass, moment = moment, **kwargs )
        return rv

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
        print "foo", self.psu.power, self.psu.max_storage
        self.refresh_engines()
        for block in self.block_structure.blocks:
            for component in block.components:
                assert component.block == block
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
        rv = self.block_structure.get_components( lambda x : "engine" in x.categories and x.active )
        rv.sort( key = lambda x : x.last_usage )
        return rv
    def all_guns(self):
        rv = self.block_structure.get_components( lambda x : "gun" in x.categories and x.active )
        rv.sort( key = lambda x : x.last_usage )
        return rv
    def ready_guns(self):
        rv = self.block_structure.get_components( lambda x : "gun" in x.categories and x.may_activate() )
        rv.sort( key = lambda x : x.last_usage )
        return rv
    def may_fire(self):
        return bool( self.ready_guns() )
    def update(self, dt):
        super( Ship, self ).update()
        if self.minimap_symbol_sprite:
            self.minimap_symbol_sprite.position = self.position
        if self._shooting:
            self.world.shoot_bullet( self )
        self.body.reset_forces()
        spin = self._spin
        if spin == 0:
            k = 1.0
            if self.body.angular_velocity > k:
                spin = 1
            elif self.body.angular_velocity < -k:
                spin = -1
            else:
                self.body.angular_velocity = 0
        rotation_force = Vec2d(self.turn_power,0) * spin
        rotation_offset = Vec2d(0,100)
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

class Debris (physics.Thing):
    def __init__(self, world, layer, position, shape, sprite, mass = 1.0, moment = 1.0, **kwargs):
        super( Debris, self ).__init__( world, shape, mass, moment, **kwargs )
        graphics.Sprite( sprite, self, layer )
        self.position = position
#        f = self.sprite.cocos_sprite.draw
#        self.sprite.cocos_sprite.draw = lambda : (f(), graphics.draw_thing_shapes(self))
        self.sprite.cocos_sprite.draw = lambda : graphics.draw_thing_shapes(self)
    def update(self):
        super( Debris, self ).update()

