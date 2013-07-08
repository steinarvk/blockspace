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
    speed = 500
    rv.position = shooter.position + shooter.direction * shooter._gun_distance
    rv.velocity = shooter.velocity + shooter.direction * (speed)
    rv.angle_radians = degrees_to_radians( shooter.angle_degrees + 90.0 )
    return rv
    
def main():
    pygame.init()
    screen = pygame.display.set_mode( (800,600) )
    window = graphics.Window()
    window.sim = physics.PhysicsSimulator()
    camera = graphics.Camera( window )
    scene = graphics.Scene( window )
    graphics.Layer( scene, cocos.layer.ColorLayer( 0, 0, 0, 1 ) )
    for i in range(8):
        graphics.Layer( scene, graphics.BackgroundCocosLayer( camera, 10.0 + 0.5 * i, "starfield{0}.png".format(i) ) )
    main_layer = graphics.Layer( scene )
    main_layer.cocos_layer.position = camera.offset()
    player = create_ship_thing( window.sim, main_layer, (0,0) )
    npc = create_ship_thing( window.sim, main_layer, (500,0), big = True )
    squareImg = pyglet.image.load( "element_red_square.png" )
    bulletImg = pyglet.image.load( "laserGreen.png" )
    batch = cocos.batch.BatchNode()
    main_layer.cocos_layer.add( batch )
    objects = []
    for i in range(200):
        cols = "red", "purple", "grey", "blue", "green", "yellow"
        sq = create_square_thing( window.sim, None, (100,0), squareImg )
        sq.position = (random.random()-0.5) * 4000, (random.random()-0.5) * 4000
        sq.angle_radians = random.random() * math.pi * 2
        sq.mylabel = sq.position
        sq.velocity = (300,10)
        batch.add( sq.sprite.cocos_sprite )
        objects.append( sq.sprite )
    input_layer = graphics.Layer( scene, gameinput.CocosInputLayer() )
    input_layer.cocos_layer.set_key_press_hook( key.SPACE, player.on_fire_key )
    for k in (key.LEFT, key.RIGHT, key.UP, key.DOWN):
        input_layer.cocos_layer.set_key_hook( k, player.on_controls_state )
    input_layer.cocos_layer.set_key_hook( k, player.on_controls_state )
    input_layer.cocos_layer.set_key_hook( key.LSHIFT, player.on_controls_state )
    physics_objects = []
    def shoot_bullet(*args, **kwargs):
        if player.may_fire():
            sq = create_bullet_thing( window.sim, bulletImg, player )
            sq.ttl = 1.5
            objects.append( sq.sprite )
            batch.add( sq.sprite.cocos_sprite )
            physics_objects.append( sq )
            player.fired()
    def npc_shoot_bullet(*args, **kwargs):
        if npc.may_fire():
            sq = create_bullet_thing( window.sim, bulletImg, npc )
            sq.ttl = 1.5
            objects.append( sq.sprite )
            batch.add( sq.sprite.cocos_sprite )
            physics_objects.append( sq )
            npc.fired()
    def on_mouse_motion( x, y, dx, dy ):
        xy = cocos.director.director.get_virtual_coordinates( x, y )
        xy = (x - camera.focus[0], y - camera.focus[1])
        things = [shape.thing for shape in window.sim.space.point_query( xy ) ]
    input_layer.cocos_layer.mouse_motion_hooks.append( on_mouse_motion )
    input_layer.cocos_layer.set_key_press_hook( key.SPACE, shoot_bullet )
    camera.following = player
    main_layer.camera = camera
    scene.schedule( lambda dt : (camera.update(dt),scene.update()) )
    player.mylabel = -1
    def update_physics_objects(dt):
        tbr = []
        for o in physics_objects:
            o.ttl -= dt
            if o.ttl <= 0.0:
                o.kill()
            if not o.alive:
                tbr.append( o )
        for o in tbr:
            physics_objects.remove(o)
    scene.schedule( lambda dt : (player.update(dt),ai_seek_target(dt,npc,player,npc_shoot_bullet),npc.update(dt),update_physics_objects(dt),window.sim.tick(dt)) )
    def update_display_objects():
        # This is the hungry line. If we can find a way to
        # only update sprites when they're actually on screen,
        # we're probably good.
        # We also need to update
        x, y = camera.focus
        hw, hh = 0.5 * window.width, 0.5 * window.height
        screen_slack = 100.0
        beyond_slack = screen_slack + 500.0
        screen_bb = pymunk.BB(x-hw-screen_slack,y-hh-screen_slack,x+hw+screen_slack,y+hh+screen_slack)
        big_bb = pymunk.BB(x-hw-beyond_slack,y-hh-beyond_slack,x+hw+beyond_slack,y+hh+beyond_slack)
        onscreen = set(window.sim.space.bb_query( screen_bb ))
        for shape in onscreen:
            shape.thing.sprite.update()
        prech = set(batch.get_children())
        for spr in objects:
            if all((shape not in onscreen for shape in spr.thing.shapes)):
                if spr.cocos_sprite in prech:
                    batch.remove( spr.cocos_sprite )
            else:
                if spr.cocos_sprite not in prech:
                    batch.add( spr.cocos_sprite )
    scene.schedule( lambda dt : update_display_objects() )
    def collide_general_with_bullet( space, arbiter ):
        anything, bullet = arbiter.shapes
        bullet.thing.ttl = min( bullet.thing.ttl, 0.05 )
#        window.sim.space.add_post_step_callback( lambda x : x.kill(), bullet.thing )
        return True
    window.sim.space.add_collision_handler( collision_type_main, collision_type_bullet, collide_general_with_bullet )
    def update_pygame():
        screen.fill( pygame.color.THECOLORS[ "black" ] )
        draw_space( screen, window.sim.space )
        pygame.display.flip()
    scene.schedule( lambda dt : update_pygame() )
    window.run( scene )

if __name__ == '__main__':
    main()
