import cocos
import sys
import pyglet
import time
import random
import math

from cocos.euclid import Vector2

from pyglet.window import key

from cocos.actions import *

from pyglet.gl import *

import pymunk

KillAction = lambda y : CallFunc( lambda x : x.kill(), y )

class LaserShot ( cocos.sprite.Sprite ):
    def __init__(self, sprite_filename, position, velocity, rotation):
        super( LaserShot, self ).__init__(sprite_filename)
        self._velocity = velocity
        self.position = position
        self.rotation = rotation
        self.lifetime = 1.0
    def tick(self, dt):
        self.position += self._velocity * dt
        self.lifetime -= dt
        self.alive = self.lifetime >= 0


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
        self.add( self.position_label )
    def tick(self, dt):
        self.position_label.element.text = "Position: {0:.2f} {1:.2f}".format( *self.game.ship.sprite.position )

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

def degrees_to_radians( degrees ):
    return math.pi * degrees / 180.0

def radians_to_degrees( radians ):
    return 180.0 * radians / math.pi

def create_convex_polygon_object( target, filename, xy, orientation, pixel_vertices, mass ):
    target.sprite = cocos.sprite.Sprite( filename )
    w, h = target.sprite.image.width, target.sprite.image.height
    px, py = xy
    vertices = [ (dx - 0.5*w, h - (dy - 0.5*h)) for (dx,dy) in pixel_vertices ]
    moment = pymunk.moment_for_poly( mass, vertices )
    target.body = pymunk.Body( mass, moment )
    target.shape = pymunk.Poly( target.body, vertices )
    target.sprite.position = xy
    target.sprite.rotation = orientation
    target.body.angle = degrees_to_radians( orientation )
    target.body.position = xy

def create_disk_object( target, filename, xy, orientation, radius, mass ):
    target.sprite = cocos.sprite.Sprite( filename )
    w, h = target.sprite.image.width, target.sprite.image.height
    px, py = xy
    moment = pymunk.moment_for_circle( mass, 0.0, radius )
    target.body = pymunk.Body( mass, moment )
    target.shape = pymunk.Circle( target.body, radius )
    target.sprite.position = xy
    target.sprite.rotation = orientation
    target.body.angle = degrees_to_radians( orientation )
    target.body.position = xy

def polar_radians( theta_radians, r ):
    return r * math.cos( theta_radians ), r * math.sin( theta_radians )

class Thing (object):
    def __init__(self):
        self.alive = True
    def tick(self, dt):
        self.sprite.rotation = radians_to_degrees( self.body.angle )
        self.sprite.position = self.body.position

class AtomicShip ( Thing ):
    def __init__(self):
        super( AtomicShip, self ).__init__()
        self._acceleration = 1000.0
        self._turnspeed = 300.0
        self._velocity = Vector2(0,0)
        self._spin = 0
        self._thrust = 0
        self.alive = True
    def control(self, state):
        self._spin = (1 if state[key.RIGHT] else 0) - (1 if state[key.LEFT] else 0)
        self._thrust = (1 if state[key.UP] else 0) - (0.5 if state[key.DOWN] else 0)
    def tick(self, dt):
        Thing.tick(self, dt)
        direction = self.sprite.rotation - 90.0
        intensity = 1000.0 * self._thrust
        fx, fy = polar_radians( degrees_to_radians(direction), intensity )
        force = (fx,-fy)
        self.body.force = force
        self.body.angle += self._spin * dt * 5
    def gunpoint(self):
        return self.sprite.position + self.orientation() * 35.0
    def orientation(self):
        return self.sprite.get_local_transform() * Vector2(0,1)
    def make_shot(self):
        shot = LaserShot( "laserGreen.png", self.gunpoint(), self.body.velocity + self.orientation() * 1000, self.sprite.rotation )
        shot.do( Delay( 2.0 ) + KillAction(shot) )
        return shot

class ShipLayer ( cocos.layer.Layer ):
    is_event_handler = True

    def __init__(self, space):
        super( ShipLayer, self ).__init__()
        self.space = space
        self.ship = AtomicShip()
#        create_convex_polygon_object( self.ship, "player.png", (320,240), 0.0, ((98,48),(59,0),(41,0),(2,48),(44,72),(55,72)), 1.0 )
        create_disk_object( self.ship, "player.png", (320,240), 0.0, 50.0, 1.0 )
        self.keyboard_state = key.KeyStateHandler()
        self.acceleration = 10
        self.velocity = Vector2(0,0)
        self.things = []
        self.add( self.ship.sprite )
        self.things.append( self.ship )
        self.space.add( self.ship.body, self.ship.shape )
        for i in range(50):
            debris = Thing()
            pos = (random.random() - 0.5) * 2000, (random.random() - 0.5) * 2000
            d = random.random() * 2 * math.pi
            s = random.random() * 20.0
            vel = s * math.cos( d ), s * math.sin( d )
            rot = random.random() * 360
#            create_convex_polygon_object( debris, "meteorBig.png", pos, rot, ((134,87),(129,39),(83,0),(24,14),(0,48),(14,84),(83,111)), 1.0 )
            create_disk_object( debris, "meteorBig.png", pos, rot, 50.0, 1.0 )
            debris.body.velocity = vel
            self.add( debris.sprite )
            self.things.append( debris )
            self.space.add( debris.body, debris.shape )
    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            self.projectile.add( self.ship.make_shot() )
        else:
            self.keyboard_state.on_key_press( symbol, modifiers )
    def on_key_release(self, symbol, modifiers):
        self.keyboard_state.on_key_release( symbol, modifiers )
    def tick(self, dt):
        self.ship.control( self.keyboard_state )
        self.space.step( dt ) # todo fix timestep
        to_remove = []
        for thing in self.things:
            if thing.alive:
                thing.tick( dt )
            else:
                to_remove.append( thing )
        for thing in to_remove:
            self.things.remove( thing )
            thing.kill()
        x, y = self.ship.sprite.position
        tx, ty = 512 - x, 384 - y
        ox, oy = self.position
        np = 0.07**dt
        self.position = (np * ox + (1-np) * tx, np * oy + (1-np) * ty)
        self.projectile.position = self.position
        self.projectile.tick( dt )

if __name__ == '__main__':
    cocos.director.director.init( width = 1024, height = 768 )
    cocos.director.director.show_FPS = True
    space = pymunk.Space()
    game = ShipLayer( space )
    game.projectile = ProjectileLayer()
    bg = BackgroundLayer( game )
    hud = HUDLayer( game )
    tut = TutorialLayer()
    scene = cocos.scene.Scene( bg, game, hud, game.projectile, tut )
    scene.schedule( game.tick )
    scene.schedule( hud.tick )
    scene.schedule( bg.tick )
    tut.add_message( "Hello world!", lambda : tut.add_message( "Have a good time!" ) )
    space.damping = 0.999
    cocos.director.director.run( scene )
