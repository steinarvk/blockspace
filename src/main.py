import graphics
import physics
import gameinput

from physics import ConvexPolygonShape, Vec2d
from gameinput import key

import cocos

import random

from util import *

class Ship (physics.Thing):
    def __init__(self, sim, layer, position, shape, sprite_name = "player.png", mass = 1.0, moment = 1.0):
        super( Ship, self ).__init__( sim, shape, mass, moment )
        graphics.Sprite( sprite_name, self, layer )
        self.body.velocity_limit = min( self.body.velocity_limit, 700.0 )
        self.position = position
        self._spin = 0
        self._thrusting = False
        self._braking = False
    def on_fire_key(self, symbol, modifiers, state):
        pass
    def on_controls_state(self, symbol, modifiers, state):
        self._spin = (1 if state[key.RIGHT] else 0) - (1 if state[key.LEFT] else 0)
        self._thrusting = state[key.UP]
        self._braking = state[key.DOWN]
    def update(self):
        super( Ship, self ).update()
        self.angular_velocity_degrees = 90.0 * self._spin
        forces = []
        if self._thrusting:
            dx, dy = polar_degrees( self.angle_degrees - 90.0, 700.0 )
            forces.append( Vec2d( dx, -dy ) )
        if self._braking:
            stopforce = self.body.velocity.normalized() * -500.0
            if self.velocity.get_length() < stopforce.get_length() * 0.01:
                forces = []
                self.body.velocity = Vec2d(0,0)
            else:
                forces.append( stopforce )
        self.body.force = reduce( lambda x,y: x+y, forces, Vec2d(0,0) )

class Debris (physics.Thing):
    def __init__(self, sim, layer, position, shape, sprite_name = "element_red_square.png", mass = 1.0, moment = 1.0):
        super( Debris, self ).__init__( sim, shape, mass, moment )
        graphics.Sprite( sprite_name, self, layer )
        self.position = position
    def update(self):
        super( Debris, self ).update()
        
def create_player_thing(sim, layer, position):
    shape = ConvexPolygonShape((98,48),(59,0),(41,0),(2,48),(44,72),(55,72))
    return Ship( sim, layer, position, shape, moment = 1.0 )

def create_square_thing(sim, layer, position, colour):
    shape = ConvexPolygonShape((0,0),(32,0),(32,32),(0,32))
    return Debris( sim, layer, position, shape, sprite_name = "element_{0}_square.png".format(colour), moment = 1.0 )
    

if __name__ == '__main__':
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
    sq = create_square_thing( window.sim, main_layer, (100,0), "red" )
    sq.velocity = (100,0)
    input_layer = graphics.Layer( scene, gameinput.CocosInputLayer() )
    input_layer.cocos_layer.set_key_press_hook( key.SPACE, player.on_fire_key )
    for k in (key.LEFT, key.RIGHT, key.UP, key.DOWN):
        input_layer.cocos_layer.set_key_hook( k, player.on_controls_state )
    camera.following = player
    main_layer.camera = camera
    scene.schedule( lambda dt : scene.update() )
    scene.schedule( lambda dt : window.sim.tick(dt) )
    scene.schedule( lambda dt : camera.update(dt) )
    scene.schedule( lambda dt : player.update() )
    scene.schedule( lambda dt : sq.update() )
    window.run( scene )
