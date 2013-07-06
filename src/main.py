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

import pygame
from pymunk.pygame_util import draw_space
import pymunk

class Ship (physics.Thing):
    def __init__(self, sim, layer, position, shape, sprite_name = "player.png", mass = 1.0, moment = 1.0):
        super( Ship, self ).__init__( sim, shape, mass, moment )
        graphics.Sprite( sprite_name, self, layer )
        self.body.velocity_limit = min( self.body.velocity_limit, 700.0 )
        self.position = position
        self._spin = 0
        self._thrusting = False
        self._braking = False
#        f = self.sprite.cocos_sprite.draw
#        self.sprite.cocos_sprite.draw = lambda : (f(), graphics.draw_thing_shapes(self))
    def on_fire_key(self, symbol, modifiers, state):
        pass
    def on_controls_state(self, symbol, modifiers, state):
        self._spin = (1 if state[key.RIGHT] else 0) - (1 if state[key.LEFT] else 0)
        self._thrusting = state[key.UP]
        self._braking = state[key.DOWN]
    def update(self):
        super( Ship, self ).update()
        self.angular_velocity_degrees = -90.0 * self._spin
        forces = []
        if self._thrusting:
            dx, dy = polar_degrees( self.angle_degrees - 90.0, 700.0 )
            forces.append( Vec2d( dx, dy ) )
        if self._braking:
            stopforce = self.body.velocity.normalized() * -500.0
            if self.velocity.get_length() < stopforce.get_length() * 0.01:
                forces = []
                self.body.velocity = Vec2d(0,0)
            else:
                forces.append( stopforce )
        self.body.force = reduce( lambda x,y: x+y, forces, Vec2d(0,0) )

class Debris (physics.Thing):
    def __init__(self, sim, layer, position, shape, sprite, mass = 1.0, moment = 1.0):
        super( Debris, self ).__init__( sim, shape, mass, moment )
        graphics.Sprite( sprite, self, layer )
        self.position = position
#        f = self.sprite.cocos_sprite.draw
#        self.sprite.cocos_sprite.draw = lambda : (f(), graphics.draw_thing_shapes(self))
        self.sprite.cocos_sprite.draw = lambda : graphics.draw_thing_shapes(self)
    def update(self):
        super( Debris, self ).update()
        
def create_player_thing(sim, layer, position):
    points = [(98,48),(59,0),(41,0),(2,48),(44,72),(55,72)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
    return Ship( sim, layer, position, shape, moment = 1.0 )

def create_square_thing(sim, layer, position, image):
    points = [(0,0),(32,0),(32,32),(0,32)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
    return Debris( sim, layer, position, shape, image, moment = 1.0 )
    
def main():
#    pygame.init()
#    screen = pygame.display.set_mode( (800,600) )
    window = graphics.Window()
    window.sim = physics.PhysicsSimulator()
    camera = graphics.Camera( window )
    scene = graphics.Scene( window )
    graphics.Layer( scene, cocos.layer.ColorLayer( 0, 0, 0, 1 ) )
    for i in range(8):
        graphics.Layer( scene, graphics.BackgroundCocosLayer( camera, 10.0 + 0.5 * i, "starfield{0}.png".format(i) ) )
    main_layer = graphics.Layer( scene )
    main_layer.cocos_layer.position = camera.offset()
    player = create_player_thing( window.sim, main_layer, (0,0) )
    img = pyglet.image.load( "element_red_square.png" )
    batch = cocos.batch.BatchNode()
    main_layer.cocos_layer.add( batch )
    objects = []
#    positions = [(window.width*0.5+500,window.height*0.5+500)]
#    for pos in positions:
    for i in range(200):
        cols = "red", "purple", "grey", "blue", "green", "yellow"
        sq = create_square_thing( window.sim, None, (100,0), img )
        sq.position = (random.random()-0.5) * 4000, (random.random()-0.5) * 4000
        sq.angle_radians = random.random() * math.pi * 2
        sq.mylabel = sq.position
        batch.add( sq.sprite.cocos_sprite )
        objects.append( sq.sprite )
    input_layer = graphics.Layer( scene, gameinput.CocosInputLayer() )
    input_layer.cocos_layer.set_key_press_hook( key.SPACE, player.on_fire_key )
    for k in (key.LEFT, key.RIGHT, key.UP, key.DOWN):
        input_layer.cocos_layer.set_key_hook( k, player.on_controls_state )
    def on_mouse_motion( x, y, dx, dy ):
        xy = cocos.director.director.get_virtual_coordinates( x, y )
        xy = (x - camera.focus[0], y - camera.focus[1])
        things = [shape.thing for shape in window.sim.space.point_query( xy ) ]
    input_layer.cocos_layer.mouse_motion_hooks.append( on_mouse_motion )
    camera.following = player
    main_layer.camera = camera
    scene.schedule( lambda dt : (camera.update(dt),scene.update()) )
    scene.schedule( lambda dt : window.sim.tick(dt) )
    scene.schedule( lambda dt : player.update() )
    player.mylabel = -1
    def update_objects():
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
    scene.schedule( lambda dt : update_objects() )
#    def update_pygame():
#        screen.fill( pygame.color.THECOLORS[ "black" ] )
#        draw_space( screen, window.sim.space )
#        pygame.display.flip()
#    scene.schedule( lambda dt : update_pygame() )
    window.run( scene )

if __name__ == '__main__':
    main()
