import cocos
import sys
import pyglet
import time
import random

from cocos.euclid import Vector2

from pyglet.window import key

from cocos.actions import *

from pyglet.gl import *

KillAction = lambda y : CallFunc( lambda x : x.kill(), y )

class LaserShot ( cocos.sprite.Sprite ):
    def __init__(self, sprite_filename, position, velocity, rotation):
        super( LaserShot, self ).__init__(sprite_filename)
        self._velocity = velocity
        self.position = position
        self.rotation = rotation
        self.alive = True
        self.lifetime = 1.0
    def tick(self, dt):
        self.position += self._velocity * dt
        self.lifetime -= dt
        self.alive = self.lifetime >= 0

class AtomicShip ( cocos.sprite.Sprite ):
    def __init__(self, sprite_filename):
        super( AtomicShip, self ).__init__( sprite_filename )
        self._acceleration = 1000.0
        self._turnspeed = 300.0
        self._velocity = Vector2(0,0)
        self._spin = 0
        self._thrust = 0
        self.alive = True
        self.image_straight = pyglet.image.load( "player.png" )
        self.image_left = pyglet.image.load( "playerLeft.png" )
        self.image_right = pyglet.image.load( "playerRight.png" )
    def control(self, state):
        self._spin = (1 if state[key.RIGHT] else 0) - (1 if state[key.LEFT] else 0)
        self._thrust = (1 if state[key.UP] else 0) - (0.5 if state[key.DOWN] else 0)
        if self._spin < 0:
            self.image = self.image_left
        elif self._spin > 0:
            self.image = self.image_right
        else:
            self.image = self.image_straight
    def tick(self, dt):
        self._velocity += self.orientation() * dt * self._acceleration * self._thrust
        self.position += self._velocity * dt
        self.rotation += dt * self._spin * self._turnspeed
    def gunpoint(self):
        return self.position + self.orientation() * 35.0
    def orientation(self):
        return self.get_local_transform() * Vector2(0,1)
    def make_shot(self):
        shot = LaserShot( "laserGreen.png", self.gunpoint(), self._velocity + self.orientation() * 1000, self.rotation )
        shot.do( Delay( 2.0 ) + KillAction(shot) )
        return shot

class BackgroundLayer ( cocos.layer.Layer ):
    def __init__(self, game):
        super( BackgroundLayer, self ).__init__()
        self.game = game
        self.bg = cocos.sprite.Sprite( "bg.png" )
        self.bg.image.get_texture() # binds texture!
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        self.add( self.bg )
    def tick(self, dt):
        self.bg.image.get_texture().tex_coords = (dt, dt, 0.0, dt + 2048, dt, 0, dt + 2048, dt + 2048, 0, dt, dt + 2048, 0 )

class HUDLayer ( cocos.layer.Layer ):
    is_event_handler = True

    def __init__(self, game):
        super( HUDLayer, self ).__init__()
        self.game = game
        self.position_label = cocos.text.Label( "Position: (0,0)", font_name = "Bitstream Vera Sans Mono", font_size = 16, anchor_x = "right", anchor_y = "bottom", color = (150,150,200,128) )
        self.position_label.position = (1015,10)
        self.speed_label = cocos.text.Label( "Speed: 0", font_name = "Bitstream Vera Sans Mono", font_size = 16, anchor_x = "right", anchor_y = "bottom", color = (150,150,200,128) )
        self.speed_label.position = (1015,30)
        self.add( self.position_label )
        self.add( self.speed_label )
    def tick(self, dt):
        self.position_label.element.text = "Position: {0:.2f} {1:.2f}".format( *self.game.ship.position )
        self.speed_label.element.text = "Speed: {0:.2f}".format( self.game.ship._velocity.magnitude() )

class TutorialLayer ( cocos.layer.Layer ):
    def __init__(self):
        super( TutorialLayer, self ).__init__()
    def add_message(self, message, cont = None):
        label = cocos.text.Label( message, font_name = "Times New Roman", font_size = 60, anchor_x = "center", anchor_y = "center", color = (100,150,150,255))
        label.position = 512,700
        self.add( label )
        label.do( Delay(2.0) + FadeOut(2.0) + KillAction(label) + CallFunc( lambda : cont() if cont else None ) )

class ProjectileLayer ( cocos.layer.Layer ):
    def __init__(self):
        super( ProjectileLayer, self ).__init__()
    def tick(self, dt):
        for child in self.get_children():
            child.tick(dt)


class ShipLayer ( cocos.layer.Layer ):
    is_event_handler = True

    def __init__(self):
        super( ShipLayer, self ).__init__()
        self.ship = AtomicShip( "player.png" )
        self.ship.position = 320,240
        self.keyboard_state = key.KeyStateHandler()
        self.acceleration = 10
        self.velocity = Vector2(0,0)
        self.things = []
        self.add_thing( self.ship )
        for i in range(50):
            debris = cocos.sprite.Sprite( "meteorBig.png" )
            debris.position = random.random() * 3000 - 1500, random.random() * 3000 - 1500
            debris.rotation = random.random() * 360
            debris.alive = True
            debris.tick = lambda x : None
            self.add_thing( debris )
    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.projectile.add( self.ship.make_shot() )
        else:
            self.keyboard_state.on_key_press( symbol, modifiers )
    def on_key_release(self, symbol, modifiers):
        self.keyboard_state.on_key_release( symbol, modifiers )
    def add_thing(self, thing):
        self.things.append( thing )
        self.add( thing )
    def tick(self, dt):
        self.ship.control( self.keyboard_state )
        to_remove = []
        for thing in self.things:
            if thing.alive:
                thing.tick( dt )
            else:
                to_remove.append( thing )
        for thing in to_remove:
            self.things.remove( thing )
            thing.kill()
        x, y = self.ship.position
        tx, ty = 512 - x, 384 - y
        ox, oy = self.position
        np = 0.07**dt
        self.position = (np * ox + (1-np) * tx, np * oy + (1-np) * ty)
        self.projectile.position = self.position
        self.projectile.tick( dt )

if __name__ == '__main__':
    cocos.director.director.init( width = 1024, height = 768 )
    cocos.director.director.show_FPS = True
    game = ShipLayer()
    game.projectile = ProjectileLayer()
    bg = BackgroundLayer( game )
    hud = HUDLayer( game )
    tut = TutorialLayer()
    scene = cocos.scene.Scene( bg, game, hud, game.projectile, tut )
    scene.schedule( game.tick )
    scene.schedule( hud.tick )
    scene.schedule( bg.tick )
    tut.add_message( "Hello world!", lambda : tut.add_message( "Have a good time!" ) )
    cocos.director.director.run( scene )
