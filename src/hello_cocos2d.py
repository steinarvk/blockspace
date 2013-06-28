import cocos
import sys
import pyglet
import time

from cocos.euclid import Vector2


from pyglet.window import key

from cocos.actions import *

class HelloWorld ( cocos.layer.Layer ):
    is_event_handler = True

    def __init__(self):
        super( HelloWorld, self ).__init__()
        self.label = cocos.text.Label( "Hello world", font_name = "Times New Roman", font_size = 32, anchor_x = "center", anchor_y = "center" )
        self.label.position = 320,240
        self.label.do( Repeat( RotateBy(360, duration=10) ) )
        self.ship = cocos.sprite.Sprite( "player.png" )
        self.ship.position = 320,240
        self.add( self.label )
        self.add( self.ship )
        self.keyboard_state = key.KeyStateHandler()
        self.acceleration = 10
        self.velocity = Vector2(0,0)
    def on_key_press(self, symbol, modifiers):
        self.keyboard_state.on_key_press( symbol, modifiers )
    def on_key_release(self, symbol, modifiers):
        self.keyboard_state.on_key_release( symbol, modifiers )
    def on_mouse_motion(self, x, y, dx, dy):
        self.label.element.text = "Hello World {0} {1}".format( x, y )
    def spin(self):
        return (1 if self.keyboard_state[key.RIGHT] else 0) - (1 if self.keyboard_state[key.LEFT] else 0)
    def thrust(self):
        return (1 if self.keyboard_state[key.UP] else 0) - (1 if self.keyboard_state[key.DOWN] else 0)
    def tick(self, dt):
        self.velocity += self.ship.get_local_transform() * Vector2(0, dt * self.acceleration * self.thrust())
        self.ship.position += self.velocity
        self.ship.rotation += dt * self.spin() * 300

if __name__ == '__main__':
    print pyglet.resource.path
    pyglet.clock
    cocos.director.director.init()
    layer = HelloWorld()
    scene = cocos.scene.Scene( layer )
    scene.schedule( layer.tick )
    cocos.director.director.run( scene )
