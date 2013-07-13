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

from operator import attrgetter

from world import World

class Ship (physics.Thing):
    def __init__(self, world, block_structure, layer, position, sprite_name = "player.png", mass = 1.0, moment = 1.0, **kwargs):
        super( Ship, self ).__init__( world, block_structure.create_collision_shape(), mass, moment, **kwargs )
        self.block_structure = block_structure
        self.block_structure.create_sprite_structure( self, layer )
#        self.sprite.add_sprite( "element_blue_square.png", (0,0) )
#        self.sprite.add_sprite( "element_purple_square.png", (0,32) )
#        self.sprite.add_sprite( "element_green_square.png", (32,0) )
#        self.sprite.add_sprite( "element_yellow_square.png", (-32,0) )
        self.body.velocity_limit = min( self.body.velocity_limit, 700.0 )
        self.body.angular_velocity_limit = degrees_to_radians( 360.0 )
        self.position = position
        self._spin = 0
        self._thrusting = False
        self._braking = False
        self._turbo_multiplier = 2
        self._thrust_power = 3500
        self._brake_power = 2500
        self._ai_time = 0.0
        self._gun_cooldown = 0.5
        self._gun_current_cooldown = 0.0
#        f = self.sprite.cocos_sprite.draw
#        self.sprite.cocos_sprite.draw = lambda : (f(), graphics.draw_thing_shapes(self))
    def on_fire_key(self, symbol, modifiers, state):
        pass
    def on_controls_state(self, symbol, modifiers, state):
        self._spin = (1 if state[key.RIGHT] else 0) - (1 if state[key.LEFT] else 0)
        self._thrusting = state[key.UP]
        self._braking = state[key.DOWN]
        self._turbo = state[key.LSHIFT]
    def may_fire(self):
        return self._gun_current_cooldown <= 0.0
    def fired(self):
        self._gun_current_cooldown = self._gun_cooldown
    def update(self, dt):
        super( Ship, self ).update()
        self._gun_current_cooldown -= dt
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
        rotation_force = Vec2d(10000,0) * spin
        rotation_offset = Vec2d(0,100)
        self.body.apply_force( rotation_force, rotation_offset )
        self.body.apply_force( -rotation_force, -rotation_offset )
        forces = []
        if self._thrusting:
            force = (self._turbo_multiplier if self._turbo else 1) * self._thrust_power
            dx, dy = polar_degrees( self.angle_degrees, force )
            forces.append( Vec2d( dx, dy ) )
        if self._braking:
            stopforce = self.body.velocity.normalized() * -1 * self._brake_power
            if self.velocity.get_length() < stopforce.get_length() * 0.01:
                forces = []
                self.body.velocity = Vec2d(0,0)
            else:
                forces.append( stopforce )
        self.body.apply_force( reduce( lambda x,y: x+y, forces, Vec2d(0,0) ) )

def ai_seek_target( dt, actor, target, fire):
    actor._ai_time += dt
    if actor._ai_time > 0.1:
        actor._ai_time = 0.0
        delta = (target.position - actor.position)
        distance = delta.get_length()
        correctness = delta.normalized().dot( actor.direction )
        actor._turbo = False
        if correctness > 0.95:
            actor._thrusting = True
            actor._braking = False
            actor._spin = 0
        else:
            actor._thrusting = False
            actor._braking = True
            actor._spin = 1
        actor._spin = 1
        if distance > 100.0 and distance < 1000.0:
            fire()

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

collision_type_main = 1
collision_type_bullet = 2
group_bulletgroup = 1

def with_gun( block, edge_index = 1 ):
    try:
        rv = block
        for index in edge_index:
            rv = with_gun( rv, index )
        return rv
    except TypeError:
        pass
    angle = [ -90.0, 0.0, 90.0, 180.0 ][ edge_index ]
    pos = Vec2d( polar_degrees( angle, 16.0 ) )
    component.PointComponent( "blaster", block, pos, angle, required_edges = (edge_index,) )
    return block

def with_guns( block ):
    return with_gun( block, range(4) )
        
def create_ship_thing(world, layer, position, shape = "small"):
    # 2
    #3 1
    # 0
    if shape == "small":
        s = blocks.BlockStructure( blocks.QuadBlock(32) )
        s.attach((0,2), with_guns(blocks.QuadBlock(32)), 0)
        s.attach((0,0), with_guns(blocks.QuadBlock(32)), 2)
        s.attach((0,1), with_guns(blocks.QuadBlock(32)), 3)
        s.attach((3,2), with_guns(blocks.QuadBlock(32)), 0)
        s.attach((3,0), with_guns(blocks.QuadBlock(32)), 2)
        s.attach((3,1), with_guns(blocks.QuadBlock(32)), 3)
    elif shape == "big":
        s = blocks.BlockStructure( blocks.QuadBlock(32) )
        s.attach((0,2), with_guns(blocks.QuadBlock(32)), 0)
        s.attach((0,0), with_guns(blocks.QuadBlock(32)), 2)
        s.attach((0,1), with_guns(blocks.QuadBlock(32)), 3)
        s.attach((3,2), with_guns(blocks.QuadBlock(32)), 0)
        s.attach((3,0), with_guns(blocks.QuadBlock(32)), 2)
        s.attach((3,1), with_guns(blocks.QuadBlock(32)), 3)
    elif shape == "single":
        s = blocks.BlockStructure( with_guns( blocks.QuadBlock(32) ) )
    elif shape == "wide":
        s = blocks.BlockStructure( blocks.QuadBlock(32) )
        s.attach((0,1), with_guns(blocks.QuadBlock(32)), 3)
        l, r = 0, 0
        for i in range(6):
            l = s.attach((l,2), with_guns(blocks.QuadBlock(32)), 0)
            r = s.attach((r,0), with_guns(blocks.QuadBlock(32)), 2)
        l = s.attach((l,2), with_guns(blocks.QuadBlock(32)), 0)
        r = s.attach((r,0), with_guns(blocks.QuadBlock(32)), 2)
    elif shape == "long":
        s = blocks.BlockStructure( blocks.QuadBlock(32) )
        l, r = 0, 0
        for i in range(6):
            l = s.attach((l,3), with_guns(blocks.QuadBlock(32)), 1)
            r = s.attach((r,1), with_guns(blocks.QuadBlock(32)), 3)
    else:
        s = shape
    s.zero_centroid()
    for block, col in zip(s.blocks,cycle(("blue","purple","green","yellow"))):
        block.image_name = "element_{0}_square.png".format( col )
    rv = Ship( world, s, layer, position, mass = len(s.blocks), moment = 20000.0, collision_type = collision_type_main )
    rv._gun_distance = 65
    return rv

def create_square_thing(world, layer, position, image):
    points = [(0,0),(32,0),(32,32),(0,32)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
    moment = pymunk.moment_for_poly( 1.0, shape.vertices )
    return Debris( world, layer, position, shape, image, moment = moment, collision_type = collision_type_main )

def create_bullet_thing(world, image, shooter, gun):
    points = [(0,0),(9,0),(9,33),(0,33)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
#    shape = DiskShape(5) # useful for debugging with pygame to see bullet origins
    layer = None
    rv = Debris( world, layer, (0,0), shape, image, mass = 1.0, moment = physics.infinity, collision_type = collision_type_bullet, group = group_bulletgroup )
    speed = 1400
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
    def __init__(self, resolution = (1300,1000), use_pygame = False, **kwargs):
        super( MainWorld, self ).__init__( **kwargs)
        self.setup_graphics( resolution )
        self.setup_game()
        self.setup_input()
        self.camera.following = self.player
        self.main_layer.camera = self.camera
        if use_pygame:
            self.setup_pygame( resolution )
            self.display.add_anonymous_hook( self.update_pygame )
        self.pre_display.add_anonymous_hook( self.update_display_objects )
        self.pre_physics.add_anonymous_hook( self.update_camera )
        self.display.add_anonymous_hook( self.scene.update )
        self.pre_physics.add_hook( self.player, self.player.update )
        self.pre_physics.add_hook( self.enemy, lambda dt : ai_seek_target( dt, self.enemy, self.player, partial( self.shoot_bullet, self.enemy ) ) )
        self.pre_physics.add_hook( self.enemy, self.enemy.update )
        self.post_physics.add_anonymous_hook( ignore_arguments( self.sim.perform_removals ) )
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
        self.main_layer = graphics.Layer( self.scene )
        self.main_layer.cocos_layer.position = self.camera.offset()
    def setup_game(self):
        self.sim = physics.PhysicsSimulator( timestep = None )
        self.player = create_ship_thing( self, self.main_layer, (300,300), shape = "wide" )
        self.enemy = create_ship_thing( self, self.main_layer, (500,500), shape = "long" )
        self.enemy.invulnerable = False
        self.img_square = pyglet.image.load( "element_red_square.png" )
        self.img_bullet = pyglet.image.load( "laserGreen.png" )
        self.batch = cocos.batch.BatchNode()
        self.main_layer.cocos_layer.add( self.batch )
        self.display_objects = []
        self.physics_objects = []
        for i in range(200):
            cols = "red", "purple", "grey", "blue", "green", "yellow"
            sq = create_square_thing( self, None, (100,0), self.img_square )
            sq.position = (random.random()-0.5) * 4000, (random.random()-0.5) * 4000
            sq.angle_radians = random.random() * math.pi * 2
            sq.mylabel = sq.position
            sq.velocity = (300,10)
            self.batch.add( sq.sprite.cocos_sprite )
            self.display_objects.append( sq.sprite )
        self.sim.space.add_collision_handler( collision_type_main, collision_type_bullet, self.collide_general_with_bullet )
    def setup_input(self):
        input_layer = graphics.Layer( self.scene, gameinput.CocosInputLayer() )
        for k in (key.LEFT, key.RIGHT, key.UP, key.DOWN):
            input_layer.cocos_layer.set_key_hook( k, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_hook( k, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_hook( key.LSHIFT, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_press_hook( key.SPACE, lambda *args, **kwargs: self.shoot_bullet(self.player) )
    def shoot_bullet(self, shooter):
        if shooter.may_fire():
            guns = shooter.block_structure.get_components( attrgetter("active") )
            for gun in guns:
                sq = create_bullet_thing( self, self.img_bullet, shooter, gun )
                def update_bullet( bullet, dt ):
                    if not bullet.alive:
                        return
                    bullet.ttl -= dt
                    bullet.grace -= dt
                    if bullet.ttl <= 0.0:
                        bullet.kill()
                def kill_bullet( sq ):
                    self.display_objects.remove( sq.sprite )
                    if sq.sprite.cocos_sprite in self.batch:
                        self.batch.remove( sq.sprite.cocos_sprite )
                sq.ttl = 1.5
                self.display_objects.append( sq.sprite )
                self.batch.add( sq.sprite.cocos_sprite )
                sq.kill_hooks.append( kill_bullet )
                self.pre_physics.add_hook( sq, partial(update_bullet,sq) )
            shooter.fired()
    def update_pygame(self):
        self.screen.fill( pygame.color.THECOLORS[ "black" ] )
        draw_space( self.screen, self.sim.space )
        pygame.display.flip()
    def update_display_objects(self):
        x, y = self.camera.focus
        hw, hh = 0.5 * self.window.width, 0.5 * self.window.height
        screen_slack = 100.0
        beyond_slack = screen_slack + 500.0
        screen_bb = pymunk.BB(x-hw-screen_slack,y-hh-screen_slack,x+hw+screen_slack,y+hh+screen_slack)
        big_bb = pymunk.BB(x-hw-beyond_slack,y-hh-beyond_slack,x+hw+beyond_slack,y+hh+beyond_slack)
        onscreen = set(self.sim.space.bb_query( screen_bb ))
        for shape in onscreen:
            shape.thing.sprite.update()
        prech = set(self.batch.get_children())
        for spr in self.display_objects:
            if all((shape not in onscreen for shape in spr.thing.shapes)):
                if spr.cocos_sprite in prech:
                    self.batch.remove( spr.cocos_sprite )
            else:
                if spr.cocos_sprite not in prech:
                    self.batch.add( spr.cocos_sprite )
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
        except KeyError:
            return False
        if not thing.invulnerable:
#            block.sprite = thing.block_structure.sprite_structure.replace_sprite( block.sprite, "element_grey_square.png" )
            detached_block = thing.block_structure.remove_block( index )
            detached_block.create_image = lambda : "element_grey_square.png"
            vel = detached_block.velocity
            deg = detached_block.angle_degrees
            def create_later():
                debris = create_ship_thing( self, self.main_layer, detached_block.position, shape = blocks.BlockStructure( detached_block ) )
                debris.angle_degrees = deg
                debris.velocity = vel
            self.queue_once( create_later )
            thing.mass = len( thing.block_structure.blocks )
        if len(thing.block_structure.blocks) == 0:
            thing.kill()
            self.remove_all_hooks( thing )
        bullet.thing.inert = True
        bullet.thing.ttl = min( bullet.thing.ttl, 0.05 )
        return False
    def run(self):
        self.window.run( self.scene )

if __name__ == '__main__':
    MainWorld().run()
