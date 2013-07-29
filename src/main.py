import graphics
import physics
import gameinput

from atlas import Atlas

from physics import ConvexPolygonShape, DiskShape, Vec2d
from gameinput import key

import cocos

import random

from util import *

from pyglet.gl import *

from bsc import include_build_directory
include_build_directory()

import bsgl

from functools import partial
from itertools import cycle

import pygame
from pymunk.pygame_util import draw_space
import pymunk

import blocks
import component

from operator import attrgetter

from world import World

class Ship (physics.Thing):
    def __init__(self, world, block_structure, layer, position, sprite_name = "player.png", mass = 1.0, moment = 1.0, **kwargs):
        super( Ship, self ).__init__( world, block_structure.create_collision_shape(), mass, moment, **kwargs )
        self.block_structure = block_structure
        self.layer = layer
        self.sprite = self.main_sprite_structure = self.block_structure.create_sprite_structure( layer = self.layer, thing = self )
        def recreate_sprite_structure():
            self.main_sprite_structure.kill()
            self.sprite = self.main_sprite_structure = self.block_structure.create_sprite_structure( layer = self.layer, thing = self )
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

def ai_flee_target( dt, actor, target):
    actor._ai_time += dt
    if actor._ai_time > 0.01:
        actor._ai_time = 0.0
        delta = (target.position - actor.position)
        distance = delta.get_length()
        correctness = delta.normalized().dot( -actor.direction )
        angle = radians_to_degrees( math.acos( correctness ) )
        sangle = (radians_to_degrees( math.atan2( delta.y, delta.x ) ) - actor.angle_degrees) % 360.0 - 180.0
        actor._turbo = False
        if distance < 500.0:
            forwards = angle < 90.0
        else:
            forwards = angle < 20.0
        last_spin = actor._spin
        new_spin = -sign(sangle)
        actor._spin = 0 if abs(sangle) < 15.0 else new_spin
        if forwards:
            actor._thrusting = True
            actor._braking = False
        else:
            actor._thrusting = False
            actor._braking = True

def ai_seek_target( dt, actor, target, fire):
    actor._ai_time += dt
    if actor._ai_time > 0.01:
        actor._ai_time = 0.0
        delta = (target.position - actor.position)
        distance = delta.get_length()
        correctness = delta.normalized().dot( actor.direction )
        angle = radians_to_degrees( math.acos( correctness ) )
        sangle = (radians_to_degrees( math.atan2( delta.y, delta.x ) ) - actor.angle_degrees + 180.0) % 360.0 - 180.0
        actor._turbo = False
        if distance > 500.0:
            forwards = angle < 90.0
        else:
            forwards = angle < 20.0
        last_spin = actor._spin
        new_spin = -sign(sangle)
        may_fire = target.alive and actor.may_fire() and distance < 1000.0
        if may_fire:
            # note that by using _relative_ velocity here we actually lead our target
            # we need to assume a bullet velocity
            shot_angle = (actor.direction * 1400 + actor.velocity - target.velocity).get_angle_degrees()
            aim_angle = (radians_to_degrees( math.atan2( delta.y, delta.x ) ) - shot_angle + 180.0) % 360.0 - 180.0
            actor._spin = -sign(aim_angle)
        elif new_spin != last_spin:
            actor._spin = 0 if abs(sangle) < 15.0 else new_spin
        if forwards:
            actor._thrusting = True
            actor._braking = False
        else:
            actor._thrusting = False
            actor._braking = True
        if may_fire:
            if aim_angle < 5.0:
                fire()

class Debris (physics.Thing):
    def __init__(self, world, layer, position, shape, sprite = None, mass = 1.0, moment = 1.0, **kwargs):
        super( Debris, self ).__init__( world, shape, mass, moment, **kwargs )
        if sprite:
            graphics.Sprite( sprite, self, layer )
            self.sprite.cocos_sprite.draw = lambda : graphics.draw_thing_shapes(self)
        self.position = position
#        f = self.sprite.cocos_sprite.draw
#        self.sprite.cocos_sprite.draw = lambda : (f(), graphics.draw_thing_shapes(self))
    def update(self):
        super( Debris, self ).update()

collision_type_main = 1
collision_type_bullet = 2
group_bulletgroup = 1

def with_engine( block, edge_index = 3, sprite = None ):
    try:
        rv = block
        for index in edge_index:
            rv = with_engine( rv, index, sprite = sprite )
        return rv
    except TypeError:
        pass
    angle = block.edge( edge_index ).angle_degrees
    pos = Vec2d( polar_degrees( angle, 16.0 ) )
    pos = Vec2d(0,0)
    pos = block.edge( edge_index ).midpoint()
    spr = cocos.sprite.Sprite( sprite )
    spr.scale = 0.15
    engine = component.EngineComponent( 500, block, pos, angle, required_edges = (edge_index,), category = "engine", sprite = spr )
    engine.power_usage = 50
    return block

def with_gun( block, edge_index = 1, sprite = None ):
    try:
        rv = block
        for index in edge_index:
            rv = with_gun( rv, index, sprite = sprite )
        return rv
    except TypeError:
        pass
    angle = block.edge( edge_index ).angle_degrees
    pos = Vec2d( polar_degrees( angle, 16.0 ) )
    pos = Vec2d(0,0)
    pos = block.edge( edge_index ).midpoint()
    spr = cocos.sprite.Sprite( sprite )
    spr.scale = 0.15
    gun = component.PointComponent( block, pos, angle, required_edges = (edge_index,), category = "gun", sprite = spr )
    gun.cooldown = 0.2
#    gun.cooldown = 0.1 # a LOT more powerful with lower cooldown
    gun.power_usage = (750 * gun.cooldown) * 2.0/3.0 # more reasonable power usage
    return block

def with_guns( block, sprite = None ):
    return with_gun( block, range(len(block.edges)), sprite = sprite )
        
def create_ship_thing(world, layer, position, shape = "small", hp = 1, recolour = True):
    gun_img = world.gem_images[10]
    engine_img = world.gem_images[14]
    def w_engine( b, edge_index = (3)):
        return with_engine( b, edge_index = edge_index, sprite = engine_img )
    def w_cockpit( b ):
        return b
    def w_gun( b, edge_index = 1 ):
        return with_gun( b, edge_index = edge_index, sprite = gun_img )
    def w_guns( b ):
        return with_guns( b, sprite = gun_img )
    # 2
    #3 1
    # 0
    if shape == "small":
        s = blocks.BlockStructure( w_engine(w_gun(w_cockpit(blocks.QuadBlock(32)))) )
        s.attach((0,2), w_engine(w_gun(blocks.QuadBlock(32))), 0)
        s.attach((0,0), w_engine(w_gun(blocks.QuadBlock(32))), 2)
        s.attach((0,1), w_engine(w_gun(blocks.QuadBlock(32))), 3)
    elif shape == "big":
        s = blocks.BlockStructure( w_engine(w_cockpit(blocks.QuadBlock(32))) )
        s.attach((0,2), w_engine(blocks.QuadBlock(32)), 0)
        s.attach((0,0), w_engine(blocks.QuadBlock(32)), 2)
        s.attach((0,1), w_engine(blocks.QuadBlock(32)), 3)
        s.attach((3,2), w_engine(blocks.QuadBlock(32)), 0)
        s.attach((3,0), w_engine(blocks.QuadBlock(32)), 2)
        s.attach((3,1), w_engine(w_gun(blocks.QuadBlock(32), 1)), 3)
    elif shape == "bigger":
        s = blocks.BlockStructure( w_gun(w_engine(blocks.QuadBlock(32))) )
        s.attach((0,2), w_gun(w_engine(blocks.QuadBlock(32))), 0)
        s.attach((0,0), w_gun(w_engine(blocks.QuadBlock(32))), 2)
        s.attach((0,1), w_gun(w_engine(blocks.QuadBlock(32))), 3)
        s.attach((3,2), w_gun(w_engine(blocks.QuadBlock(32))), 0)
        s.attach((3,0), w_gun(w_engine(blocks.QuadBlock(32))), 2)
        s.attach((3,1), w_gun(w_engine(blocks.QuadBlock(32))), 3)
        s.attach((6,2), w_gun(w_engine(blocks.QuadBlock(32))), 0)
        s.attach((6,0), w_gun(w_engine(blocks.QuadBlock(32))), 2)
        s.attach((6,1), w_gun(w_engine(blocks.QuadBlock(32))), 3)
    elif shape == "single":
        s = blocks.BlockStructure( w_guns( w_cockpit( blocks.QuadBlock(32) ) ) )
    elif shape == "octa":
        s = blocks.BlockStructure( w_guns( w_cockpit( blocks.OctaBlock(32) ) ) )
        for i in range(7):
            a = s.attach((0,i), blocks.QuadBlock(32), 0)
            b = s.attach((a,2), blocks.QuadBlock(32), 0)
            c = s.attach((b,2), blocks.QuadBlock(32), 0)
            d = s.attach((c,1), w_gun(blocks.QuadBlock(32), 1), 3)
    elif shape == "wide":
        s = blocks.BlockStructure( w_guns(w_engine( blocks.QuadBlock(32) )) )
        s.attach((0,1), w_engine(w_guns(blocks.QuadBlock(32))), 3)
        l, r = 0, 0
        for i in range(6):
            l = s.attach((l,2), w_guns(w_engine(blocks.QuadBlock(32))), 0)
            r = s.attach((r,0), w_guns(w_engine(blocks.QuadBlock(32))), 2)
        l = s.attach((l,2), w_guns(w_engine(blocks.QuadBlock(32))), 0)
        r = s.attach((r,0), w_guns(w_engine(blocks.QuadBlock(32))), 2)
    elif shape == "long":
        s = blocks.BlockStructure( w_cockpit( blocks.QuadBlock(32) ) )
        l, r = 0, 0
        for i in range(6):
            l = s.attach((l,3), w_guns(blocks.QuadBlock(32)), 1)
            r = s.attach((r,1), w_guns(blocks.QuadBlock(32)), 3)
    else:
        s = shape
    s.zero_centroid()
    print "ship with", len(s.blocks), "blocks has", len(s.free_edge_indices)
    if recolour:
        colours = { "blue": (0,0,255),
                    "purple": (255,0,255),
                    "white": (255,255,255),
                    "green": (0,255,0),
                    "yellow": (255,255,0),
                    "dark-gray": (64,64,64),
                    "red": (255,0,0) }
        def make_cockpit( block ):
            cockpit = component.Component( block, categories = ("generator","battery") )
            cockpit.power_capacity = int(0.5 + 0.5 * block.area())
            cockpit.power_production = int(0.5 + 0.5 * block.area())
            block.max_hp = block.hp = hp * 3
            block.colour = colours["green"]
            block.cockpit = True
        def make_battery( block ):
            battery = component.Component( block, categories = ("battery") )
            battery.power_capacity = int(block.area())
            block.colour = colours["yellow"]
        def make_generator( block ):
            generator = component.Component( block, categories = ("generator") )
            generator.power_production = int(0.5 + 0.5 * block.area())
            block.colour = colours["red"]
        def make_armour( block ):
            block.max_hp = block.hp = hp * 5
            block.colour = colours["dark-gray"]
        gens = make_battery, make_generator, make_armour
        gens = (make_armour,)
        for block in s.blocks:
            block.max_hp = block.hp = hp
            block.cockpit = False
        for block in list(s.blocks)[1:]:
            random.choice(gens)( block )
        make_cockpit( s.blocks[0] )
    rv = Ship( world, s, layer, position, mass = len(s.blocks), moment = 20000.0, collision_type = collision_type_main )
    rv._gun_distance = 65
    return rv

def create_square_thing(world, layer, position, image):
    points = [(0,0),(32,0),(32,32),(0,32)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
    moment = pymunk.moment_for_poly( 1.0, shape.vertices )
    rv = Debris( world, layer, position, shape, image, moment = moment, collision_type = collision_type_main )
    return rv

def create_bullet_thing(world, shooter, gun):
    points = [(0,0),(9,0),(9,33),(0,33)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
#    shape = DiskShape(5) # useful for debugging with pygame to see bullet origins
    layer = None
    rv = Debris( world, layer, (0,0), shape, None, mass = 1.0, moment = physics.infinity, collision_type = collision_type_bullet, group = group_bulletgroup )
    speed = 1400
#    speed = 0
    base_velocity = gun.velocity
    base_velocity = shooter.velocity # unrealistic but possibly better
    rv.velocity = base_velocity + gun.direction * speed
    rv.position = gun.position
    rv.angle_radians = degrees_to_radians( gun.angle_degrees + 90.0 ) # realistic
#    rv.angle_radians = degrees_to_radians( rv.velocity.get_angle_degrees() + 999.0 ) # might look better
    rv.inert = False
    rv.grace = 0.15
    rv.shooter = shooter
    return rv

class MainWorld (World):
    def __init__(self, resolution = (1000,800), use_pygame = False, **kwargs):
        super( MainWorld, self ).__init__( **kwargs)
        self.setup_graphics( resolution )
        self.setup_game()
        self.setup_input()
        self.setup_hud()
        self.camera.following = self.player
        self.main_layer.camera = self.camera
        if use_pygame:
            self.setup_pygame( resolution )
            self.display.add_anonymous_hook( self.update_pygame )
        self.pre_display.add_anonymous_hook( self.update_psys_managed_objects )
        self.pre_physics.add_anonymous_hook( self.update_camera )
        self.display.add_anonymous_hook( self.scene.update )
        self.player.body.velocity_limit = 800.0 # experiment with this for actually chasing fleeing ships
        self.pre_physics.add_hook( self.player, self.player.update )
        self.pre_physics.add_hook( self.enemy, lambda dt : ai_seek_target( dt, self.enemy, self.player, partial( self.shoot_bullet, self.enemy ) ) )
#        self.pre_physics.add_hook( self.enemy, lambda dt : ai_flee_target( dt, self.enemy, self.player ) )
        self.pre_physics.add_hook( self.enemy, self.enemy.update )
        self.pre_physics.add_hook( self.enemy2, lambda dt : ai_seek_target( dt, self.enemy2, self.player, partial( self.shoot_bullet, self.enemy2 ) ) )
#        self.pre_physics.add_hook( self.enemy2, lambda dt : ai_flee_target( dt, self.enemy2, self.player ) )
        self.pre_physics.add_hook( self.enemy2, self.enemy2.update )
        for gun in self.player.block_structure.get_components( lambda x : "gun" in x.categories ):
            gun.cooldown /= 2.0
        for x in (self.player, self.enemy, self.enemy2):
            self.post_physics.add_hook( x, x.tick )
            x.add_to_minimap( self.minimap, "solid_white_5x5.png", (0,255,0) if x == self.player else (255,0,0) )
#        for x in self.things:
#            x.add_to_minimap( self.minimap, "solid_white_5x5.png", (128,128,128) )
        self.physics.add_anonymous_hook( self.sim.tick )
        self.scene.schedule( self.update_everything )
    def update_everything(self, dt):
        self.tick( dt )
        self.display_update()
    def update_camera(self, dt):
        self.camera.update( dt )
    def setup_pygame(self, resolution):
        pygame.init()
        self.screen = pygame.display.set_mode( resolution )
    def setup_graphics(self, resolution):
        self.window = graphics.Window( resolution )
        self.camera = graphics.Camera( self.window )
        self.scene = graphics.Scene( self.window )
        graphics.Layer( self.scene, cocos.layer.ColorLayer( 0, 0, 0, 1 ) )
        for i in range(8):
            graphics.Layer( self.scene, graphics.BackgroundCocosLayer( self.camera, 10.0 + 0.5 * i, "starfield{0}.png".format(i) ) )
        self.hud_width = 170
        self.main_layer = graphics.Layer( self.scene )
        self.main_layer.cocos_layer.position = self.camera.offset()
        self.main_layer.size = (self.window.width-self.hud_width,self.window.height)
        self.hud_cocos_layer = graphics.BlankingCocosLayer()
        self.hud_cocos_layer.clear_colour = (0,40,40,255)
        self.hud_cocos_layer.clear_rect = ((self.window.width-self.hud_width,0),(self.window.width,0),(self.window.width,self.window.height),(self.window.width-self.hud_width,self.window.height))
        self.hud_layer = graphics.Layer( self.scene, cocos_layer = self.hud_cocos_layer )
        self.hud_layer.cocos_layer.position = 0,0
        self.gem_images = pyglet.image.ImageGrid( pyglet.image.load("gems3.png"), 4, 4 )
    def setup_hud(self):
        def update_hp_display():
            undamaged = 255,255,255
            undamaged_cockpit = 0,255,0
            damaged = damaged_cockpit = 255,0,0
            for block, sprite in self.hud_sprite.subcomponent.items():
                rel = float(block.hp) / block.max_hp
                a = damaged_cockpit if block.cockpit else damaged
                b = undamaged_cockpit if block.cockpit else undamaged
                sprite.color = vector_lerp( rel, a, b )
                cockpit = False
        def create_hp_display():
            self.hud_sprite = self.player.block_structure.create_sprite_structure( layer = self.hud_layer )
            expected_size = self.hud_width
            self.hud_sprite.node.position = self.window.width - expected_size*0.5, self.window.height - expected_size * 0.5
            self.hud_sprite.node.rotation = -90.0
            self.hud_sprite.node.scale = 0.5
            update_hp_display()
        def recreate_hp_display():
            self.hud_sprite.kill()
            create_hp_display()
        
        bar = graphics.VerticalBar( 8, 256, (0,64,0), (128,0,0) )
        bar.position = (self.window.width - self.hud_width + 16), (self.window.height - self.hud_width - bar.height)
        x, y = self.window.width - self.hud_width + 32, self.window.height - self.hud_width
        speed_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        power_supply_size_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        power_production_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        thrust_power_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        turn_power_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        brake_power_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        number_of_engines_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        number_of_guns_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        x, y = self.window.width - self.hud_width + 16, self.window.height - self.hud_width - bar.height - 16
        position_label = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        def update_labels():
            x, y = self.player.position
            position_label.element.text = "({0},{1})".format( int(x*0.1), int(y*0.1) )
            speed_label.element.text = "S: {0:.1f}".format( self.player.speed )
            power_production_label.element.text = "PP: {0}".format( int(sum( self.player.psu.production.values() ) ) )
            power_supply_size_label.element.text = "MP: {0}".format( int(self.player.psu.max_storage) )
            thrust_power_label.element.text = "T: {0}".format( self.player.thrust_power )
            turn_power_label.element.text = "R: {0}".format( self.player.turn_power )
            brake_power_label.element.text = "B: {0}".format( self.player.brake_power )
            number_of_engines_label.element.text = "#E: {}".format( len( self.player.all_engines() ) )
            number_of_guns_label.element.text = "#E: {0}/{1}".format( len( self.player.ready_guns() ), len( self.player.all_guns() ) )
        def update_power_display():
            bar.fill = self.player.psu.charge_rate()
        self.hud_cocos_layer.add( bar )
        self.minimap = graphics.Minimap( self.hud_width - 32, self.hud_width - 32, 5000, 5000, self.player )
        self.minimap.position = (self.window.width - self.hud_width + 16), (self.window.height - self.hud_width - bar.height - self.hud_width - 16)
        self.hud_cocos_layer.add( self.minimap )
        def update_hud():
            update_labels()
            update_hp_display()
            update_power_display()
            self.minimap.update()
        create_hp_display()
        self.post_physics.add_anonymous_hook( ignore_arguments( update_hud ) )
        self.player.reshape_hooks.add_anonymous_hook( recreate_hp_display )
    def setup_game(self):
        self.sim = physics.PhysicsSimulator( timestep = None )
        self.player = create_ship_thing( self, self.main_layer, (300,300), shape = "bigger", hp = 5 )
        self.player.invulnerable = False
        self.enemy = create_ship_thing( self, self.main_layer, (500,500), shape = "small", hp = 0 )
        self.enemy.invulnerable = False
        self.enemy.body.angular_velocity_limit = degrees_to_radians(144*2)
        self.enemy2 = create_ship_thing( self, self.main_layer, (0,500), shape = "small", hp = 0 )
        self.enemy2.invulnerable = False
        self.enemy2.body.angular_velocity_limit = degrees_to_radians(144*2)
        self.enemy.angle_degrees = random.random() * 360.0
        self.enemy2.angle_degrees = random.random() * 360.0
        self.atlas = Atlas( "atlas.generated" )
        self.object_psys = bsgl.System( texture_id = self.atlas.sheet.get_texture().id )
        self.batch = cocos.batch.BatchNode()
        self.main_layer.cocos_layer.add( self.batch )
        self.physics_objects = []
        self.things = []
        self.psys_managed_things = {}
        for i in range(200):
            cols = "red", "purple", "grey", "blue", "green", "yellow"
            sq = create_square_thing( self, None, (100,0), None )
            sq.position = (random.random()-0.5) * 4000, (random.random()-0.5) * 4000
            sq.angle_radians = random.random() * math.pi * 2
            sq.mylabel = sq.position
            sq.velocity = (30,10)
            kw = {}
            name = "polygon_normals.4.generated"
            kw[ "size" ] = (32.0/128.0,32.0/128.0)
            kw[ "texture_coordinates" ] = self.atlas.texcoords( name )
            kw[ "texture_size" ] = self.atlas.texsize( name )
            z = random.random() * 6.28
            r = 0.1 + random.random() * 10.0
            pos = r*math.cos(z), r*math.sin(z)
            # need to translate from pixel space
            # [0,self.
            # to
            # [-1.3333,1.3333] x [-1,1]
            p = sq.position
            p = p + self.main_layer.cocos_layer.position
            p = Vec2d(p) / Vec2d( self.window.width, self.window.height )
            p = (p * 2) - Vec2d(1,1)
            p = p * Vec2d( self.window.width / float(self.window.height), 1 ) 
            kw[ "position" ] = p
            kw[ "angle" ] = sq.angle_radians
            kw[ "colour" ] = 1.0, 0.5, 0.5, 1.0
            index = self.object_psys.add( **kw )
            self.psys_managed_things[ sq ] = index
            self.things.append( sq )
        def draw_psys():
            glEnable( GL_SCISSOR_TEST )
            glScissor( 0, 0, self.window.width + 1 - self.hud_width, self.window.height )
            self.object_psys.draw()
            glDisable( GL_SCISSOR_TEST )
        graphics.Layer( self.scene, cocos_layer = graphics.FunctionCocosLayer( draw_psys ) )
        print self.display.hooks
        self.sim.space.add_collision_handler( collision_type_main, collision_type_bullet, self.collide_general_with_bullet )
    def setup_input(self):
        input_layer = graphics.Layer( self.scene, gameinput.CocosInputLayer() )
        for k in (key.LEFT, key.RIGHT, key.UP, key.DOWN):
            input_layer.cocos_layer.set_key_hook( k, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_hook( k, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_hook( key.LSHIFT, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_press_hook( key.SPACE, lambda *args, **kwargs: (self.player.on_controls_state(*args,**kwargs), self.shoot_bullet(self.player)) )
        input_layer.cocos_layer.set_key_release_hook( key.SPACE, lambda *args, **kwargs: self.player.on_controls_state(*args,**kwargs) )
    def shoot_bullet(self, shooter):
        guns = shooter.ready_guns()
        index = 0
        for gun in guns:
            if not gun.may_activate():
                continue
            gun.activated( index )
            sq = create_bullet_thing( self, shooter, gun )
            kw = {}
            kw[ "size" ] = Vec2d(9.0/self.window.height, 33.0/self.window.height) * 2
            kw[ "texture_size" ] = self.atlas.texsize( "laserGreen" )
            kw[ "texture_coordinates" ] = self.atlas.texcoords( "laserGreen" )
            kw[ "position" ] = self.silly_software_transform( sq.position )
            kw[ "angle" ] = sq.angle_radians
            kw[ "colour" ] = (0.0,1.0,0.0,1.0)
            sq.index = self.object_psys.add( **kw )
            self.psys_managed_things[ sq ] = sq.index
            def update_bullet( bullet, dt ):
                if not bullet.alive:
                    return
                bullet.ttl -= dt
                bullet.grace -= dt
                if bullet.ttl <= 0.0:
                    bullet.kill()
            def kill_bullet( sq ):
                del self.psys_managed_things[ sq ]
                self.object_psys.remove( sq.index )
            sq.ttl = 1.5
            sq.kill_hooks.append( kill_bullet )
            self.pre_physics.add_hook( sq, partial(update_bullet,sq) )
            index += 1
    def update_pygame(self):
        self.screen.fill( pygame.color.THECOLORS[ "black" ] )
        draw_space( self.screen, self.sim.space )
        pygame.display.flip()
    def update_psys_managed_objects(self):
        for thing, index in self.psys_managed_things.items():
            self.object_psys.update_position_and_angle( index, self.silly_software_transform( thing.position ), thing.angle_radians )

    def silly_software_transform(self, p):
        p = p + self.main_layer.cocos_layer.position
        p = Vec2d(p) / Vec2d( self.window.width, self.window.height )
        p = (p * 2) - Vec2d(1,1)
        p = p * Vec2d( self.window.width / float(self.window.height), 1 ) 
        return p

    def collide_general_with_bullet(self, space, arbiter ):
        anything, bullet = arbiter.shapes
        try:
            thing = anything.thing
            index = anything.extra_info
        except AttributeError:
            bullet.thing.ttl = min( bullet.thing.ttl, 0.05 )
            return False
        if bullet.thing.inert:
            return False
        if (bullet.thing.shooter == thing) and bullet.thing.grace > 0.0:
            return False
        try:
            block = thing.block_structure.blocks[ index ]
            hp = block.hp
        except KeyError:
            return False
        except AttributeError:
            return False
        if not thing.invulnerable:
            block.hp = hp - 1
            if block.hp <= 0:
                detached_block = thing.block_structure.remove_block( index )
                detached_block.detach_components( thing )
                detachable_blocks = []
                detached_parts = []
                if index == 0:
                    survivor = None
                    for index, block in thing.block_structure.blocks.indexed():
                            if index != 0:
                                detachable_blocks.append( index )
                else:
                    survivor = thing.block_structure.any_block_index()
                    if survivor != None:
                        survivors = thing.block_structure.connectivity_set_of( survivor )
                        for index, block in thing.block_structure.blocks.indexed():
                            if index not in survivors:
                                detachable_blocks.append( index )
                while detachable_blocks:
                    x = thing.block_structure.connectivity_set_of( detachable_blocks.pop(0) )
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
                        debris = create_ship_thing( self, self.main_layer, pos, shape = blocks.BlockStructure( detached_block ), recolour = False )
                        debris.angle_degrees = deg
                        debris.velocity = vel
                    self.queue_once( create_later )
                on_detached_single_block( detached_block )
                for detached_part in detached_parts:
                    # this must be amended to reconstruct the connections
                    for index in detached_part:
                        db = thing.block_structure.remove_block( index )
                        db.detach_components( thing )
                        on_detached_single_block( db )
                if survivor != None:
                    remaining_block = thing.block_structure.blocks[survivor]
                    wpv = [(1,b.position-thing.position,b.velocity) for b in thing.block_structure.blocks ]
                    pos_before = remaining_block.position
                    angle_before = remaining_block.angle_degrees
                    thing.block_structure.zero_centroid()
                    thing.block_structure.clear_collision_shape()
                    thing.reshape( thing.block_structure.create_collision_shape() )
                    pos_after = remaining_block.position
                    angle_after = remaining_block.angle_degrees
                    thing.position -= (pos_after - pos_before)
                    linear, rotational = physics.calculate_velocities( wpv )
                    thing.velocity = linear
                    thing.angular_velocity = rotational
                    pos_after = remaining_block.position
                    angle_after = remaining_block.angle_degrees
                    assert degrees_almost_equal( angle_after, angle_before )
                    assert vectors_almost_equal( pos_before, pos_after )
                thing.mass = len( thing.block_structure.blocks )
        if len(thing.block_structure.blocks) == 0:
            thing.kill()
        bullet.thing.inert = True
        bullet.thing.ttl = min( bullet.thing.ttl, 0.05 )
        return False
    def run(self):
        self.window.run( self.scene )

if __name__ == '__main__':
    MainWorld().run()
