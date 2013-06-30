import graphics
import physics

from physics import ConvexPolygonShape

import cocos

import random

def create_player_thing(sim, layer, position):
    shape = ConvexPolygonShape((98,48),(59,0),(41,0),(2,48),(44,72),(55,72))
    player = physics.Thing( sim, shape, mass = 1.0, moment = 1.0 )
    graphics.Sprite( "player.png", player, layer )
    return player

if __name__ == '__main__':
    window = graphics.Window()
    window.sim = physics.PhysicsSimulator()
    scene = graphics.Scene( window )
    main_layer = graphics.Layer( scene )
    player = create_player_thing( window.sim, main_layer, (0,0) )
    player.velocity = (100,0)
    scene.schedule( lambda dt : scene.update() )
    scene.schedule( lambda dt : window.sim.tick(dt) )
    window.run( scene )
