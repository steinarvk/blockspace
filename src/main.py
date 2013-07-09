import graphics
import physics
import gameinput

from physics import ConvexPolygonShape, Vec2d
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

from world import World

class Ship (physics.Thing):
    def __init__(self, sim, block_structure, layer, position, sprite_name = "player.png", mass = 1.0, moment = 1.0, **kwargs):
        super( Ship, self ).__init__( sim, physics.zero_shape_centroid( block_structure.create_collision_shape() ), mass, moment, **kwargs )
        self.block_structure = block_structure
        self.block_structure.create_sprite_structure( self, layer )
#        self.sprite.add_sprite( "element_blue_square.png", (0,0) )
#        self.sprite.add_sprite( "element_purple_square.png", (0,32) )
#        self.sprite.add_sprite( "element_green_square.png", (32,0) )
#        self.sprite.add_sprite( "element_yellow_square.png", (-32,0) )
        self.body.velocity_limit = min( self.body.velocity_limit, 700.0 )
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
        self.angular_velocity_degrees = -300.0 * self._spin
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
        self.body.force = reduce( lambda x,y: x+y, forces, Vec2d(0,0) )

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
        if distance > 100.0 and distance < 1000.0:
            fire()

class Debris (physics.Thing):
    def __init__(self, sim, layer, position, shape, sprite, mass = 1.0, moment = 1.0, **kwargs):
        super( Debris, self ).__init__( sim, shape, mass, moment, **kwargs )
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
        
def create_ship_thing(sim, layer, position, big = False):
    s = blocks.BlockStructure( blocks.QuadBlock(32) )
    s.attach((0,1), blocks.QuadBlock(32), 0)
    s.attach((0,0), blocks.QuadBlock(32), 0)
    s.attach((0,2), blocks.QuadBlock(32), 0)
    if big:
        s.attach((1,2), blocks.QuadBlock(32), 0)
        s.attach((1,1), blocks.QuadBlock(32), 0)
        s.attach((1,3), blocks.QuadBlock(32), 0)
    for block, col in zip(s.blocks,cycle(("blue","purple","green","yellow"))):
        block.image_name = "element_{0}_square.png".format( col )
    rv = Ship( sim, s, layer, position, mass = len(s.blocks), moment = 4000.0, collision_type = collision_type_main )
    rv._gun_distance = 65
    if big:
        rv._gun_distance += 32
    return rv

def create_square_thing(sim, layer, position, image):
    points = [(0,0),(32,0),(32,32),(0,32)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
    moment = pymunk.moment_for_poly( 1.0, shape.vertices )
    return Debris( sim, layer, position, shape, image, moment = moment, collision_type = collision_type_main )

def create_bullet_thing(sim, image, shooter):
    points = [(0,0),(9,0),(9,33),(0,33)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
    layer = None
    rv = Debris( sim, layer, (0,0), shape, image, mass = 1.0, moment = physics.infinity, collision_type = collision_type_bullet, group = group_bulletgroup )
    speed = 700
    rv.position = shooter.position + shooter.direction * shooter._gun_distance
    rv.velocity = shooter.velocity + shooter.direction * (speed)
    rv.angle_radians = degrees_to_radians( shooter.angle_degrees + 90.0 )
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
        self.pre_physics.add_anonymous_hook( self.update_physics_objects )
        self.pre_display.add_anonymous_hook( self.update_display_objects )
        self.pre_physics.add_anonymous_hook( self.update_camera )
        self.display.add_anonymous_hook( self.scene.update )
        self.pre_physics.add_hook( self.player, self.player.update )
        self.pre_physics.add_hook( self.enemy, lambda dt : ai_seek_target( dt, self.enemy, self.player, partial( self.shoot_bullet, self.enemy ) ) )
        self.pre_physics.add_hook( self.enemy, self.enemy.update )
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
        self.player = create_ship_thing( self.sim, self.main_layer, (0,0) )
        self.enemy = create_ship_thing( self.sim, self.main_layer, (500,0), big = True )
        self.img_square = pyglet.image.load( "element_red_square.png" )
        self.img_bullet = pyglet.image.load( "laserGreen.png" )
        self.batch = cocos.batch.BatchNode()
        self.main_layer.cocos_layer.add( self.batch )
        self.display_objects = []
        self.physics_objects = []
        for i in range(200):
            cols = "red", "purple", "grey", "blue", "green", "yellow"
            sq = create_square_thing( self.sim, None, (100,0), self.img_square )
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
            sq = create_bullet_thing( self.sim, self.img_bullet, shooter )
            sq.ttl = 1.5
            self.display_objects.append( sq.sprite )
            self.batch.add( sq.sprite.cocos_sprite )
            self.physics_objects.append( sq )
            shooter.fired()
    def update_physics_objects(self, dt):
        tbr = []
        for o in self.physics_objects:
            o.ttl -= dt
            if o.ttl <= 0.0:
                o.kill()
            if not o.alive:
                tbr.append( o )
        for o in tbr:
            self.physics_objects.remove(o)
    def update_pygame(self):
        self.screen.fill( pygame.color.THECOLORS[ "black" ] )
        draw_space( self.screen, self.sim )
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
        bullet.thing.ttl = min( bullet.thing.ttl, 0.05 )
        return True
    def run(self):
        self.window.run( self.scene )

if __name__ == '__main__':
    MainWorld().run()
