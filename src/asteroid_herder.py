import cocos
import sys
import pyglet
import time
import random
import math
import ctypes

from util import degrees_to_radians, radians_to_degrees

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
        self.image = pyglet.image.load( "brushwalker437.png" )
        self.texture = self.image.get_texture()
        glBindTexture( self.texture.target, self.texture.id )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        self.t = 0.0
    def draw(self):
        x, y = self.game.position
        s = 1024
        bs = -1 / float(s)
        x, y = (x*bs,y*bs)
        glEnable( self.texture.target )
        glColor4f( 0.3, 0.3, 0.3, 1.0 ) 
        glBindTexture( GL_TEXTURE_2D, self.texture.id )
        glPushMatrix()
        self.transform()
        glBegin( GL_QUADS )
        glTexCoord2f( x, y )
        glVertex2i( 0, 0 )
        glTexCoord2f( x + 1, y )
        glVertex2i( 1024, 0 )
        glTexCoord2f( x + 1, y + 1 )
        glVertex2i( 1024, 1024 )
        glTexCoord2f( x, y + 1 )
        glVertex2i( 0, 1024 )
        glEnd()
        glPopMatrix()
    def tick(self, dt):
        self.t += dt * 0.1

class HUDLayer ( cocos.layer.Layer ):
    is_event_handler = True

    def __init__(self, game):
        super( HUDLayer, self ).__init__()
        self.game = game
        self.tracking_label = cocos.text.Label( "", font_name = "Bitstream Vera Sans Mono", font_size = 16, anchor_x = "right", anchor_y = "bottom", color = (150,150,200,128) )
        self.tracking_label.position = (1015,730)
        self.add( self.tracking_label )
        self.tracking_position_label = cocos.text.Label( "", font_name = "Bitstream Vera Sans Mono", font_size = 16, anchor_x = "right", anchor_y = "bottom", color = (150,150,200,128) )
        self.tracking_position_label.position = (1015,700)
        self.add( self.tracking_position_label )
        self.tracking_velocity_label = cocos.text.Label( "", font_name = "Bitstream Vera Sans Mono", font_size = 16, anchor_x = "right", anchor_y = "bottom", color = (150,150,200,128) )
        self.tracking_velocity_label.position = (1015,670)
        self.add( self.tracking_velocity_label )
        self.tracking_speed_label = cocos.text.Label( "", font_name = "Bitstream Vera Sans Mono", font_size = 16, anchor_x = "right", anchor_y = "bottom", color = (150,150,200,128) )
        self.tracking_speed_label.position = (1015,640)
        self.add( self.tracking_speed_label )
        self.position_label = cocos.text.Label( "Position: ", font_name = "Bitstream Vera Sans Mono", font_size = 16, anchor_x = "right", anchor_y = "bottom", color = (150,150,200,128) )
        self.position_label.position = (1015,10)
        self.add( self.position_label )
        self.velocity_label = cocos.text.Label( "Velocity: ", font_name = "Bitstream Vera Sans Mono", font_size = 16, anchor_x = "right", anchor_y = "bottom", color = (150,150,200,128) )
        self.velocity_label.position = (1015,40)
        self.add( self.velocity_label )
        self.speed_label = cocos.text.Label( "Speed: ", font_name = "Bitstream Vera Sans Mono", font_size = 16, anchor_x = "right", anchor_y = "bottom", color = (150,150,200,128) )
        self.speed_label.position = (1015,70)
        self.add( self.speed_label )
    def tick(self, dt):
        self.position_label.element.text = "Position: {0:.2f} {1:.2f}".format( *self.game.ship.body.position )
        self.velocity_label.element.text = "Velocity: {0:.2f} {1:.2f}".format( *self.game.ship.body.velocity )
        self.speed_label.element.text = "Speed: {0:.2f}".format( self.game.ship.body.velocity.get_length() )
        if self.game.tracking:
            self.tracking_label.element.text = self.game.tracking.name
            self.tracking_position_label.element.text = "Position: {0:.2f} {1:.2f}".format( *self.game.tracking.body.position )
            self.tracking_velocity_label.element.text = "Velocity: {0:.2f} {1:.2f}".format( *self.game.tracking.body.velocity )
            self.tracking_speed_label.element.text = "Speed: {0:.2f}".format( self.game.tracking.body.velocity.get_length() )
        else:
            self.tracking_label.element.text = ""
            self.tracking_position_label.element.text = ""
            self.tracking_velocity_label.element.text = ""
            self.tracking_speed_label.element.text = ""
            

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

def create_convex_polygon_object( target, filename, xy, orientation, pixel_vertices, mass ):
    target.sprite = cocos.sprite.Sprite( filename )
    w, h = target.sprite.image.width, target.sprite.image.height
    px, py = xy
    vertices = [ (dx - 0.5*w, 0.5 * h - dy) for (dx,dy) in pixel_vertices ]
    moment = pymunk.moment_for_poly( mass, vertices )
    target.body = pymunk.Body( mass, moment )
    target.shape = pymunk.Poly( target.body, vertices )
    target.sprite.position = xy
    target.sprite.rotation = orientation
    target.body.angle = degrees_to_radians( orientation )
    target.body.position = xy
    target.shape.thing = target

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
    target.shape.thing = target

def polar_radians( theta_radians, r ):
    return r * math.cos( theta_radians ), r * math.sin( theta_radians )

class Thing (object):
    def __init__(self):
        self.name = "Thing"
        self.alive = True
    def tick(self, dt):
        self.sprite.rotation = radians_to_degrees( self.body.angle )
        self.sprite.position = self.body.position

class AtomicShip ( Thing ):
    def __init__(self):
        super( AtomicShip, self ).__init__()
        self.name = "Spaceship"
        self._acceleration = 1000.0
        self._turnspeed = 300.0
        self._velocity = Vector2(0,0)
        self._spin = 0
        self._thrust = 0
        self._braking = 0
        self._max_speed = 800.0
        # sort of required not to break the physics sim
        # idea if we want to preserve the space feel:
        # set the max speed very high (but at some point where we can still reliably do collisions)
        # when at 50% of the max speed, you start taking damage, and you'll never be able to reach 100%.
        self.alive = True
    def control(self, state):
        self._spin = (1 if state[key.RIGHT] else 0) - (1 if state[key.LEFT] else 0)
        self._thrust = (1 if state[key.UP] else 0)
        self._braking = state[key.DOWN]
    def tick(self, dt):
        Thing.tick(self, dt)
        direction = self.sprite.rotation - 90.0
        intensity = 1000.0 * self._thrust
        fx, fy = polar_radians( degrees_to_radians(direction), intensity )
        thrust_force = (fx,-fy)
        self.body.force = thrust_force
        self.body.angle += self._spin * dt * 5
        l = self.body.velocity.get_length()
        changed = False
        if self._braking:
            l -= 700.0 * dt
            if l < 0.0:
                l = 0.0
            changed = True
        if l > self._max_speed:
            l = self._max_speed
        self.body.velocity = self.body.velocity.normalized() * l
    def gunpoint(self):
        return self.sprite.position + self.orientation() * 35.0
    def gunpoint_left(self):
        orient = self.orientation()
        return self.sprite.position + orient * 10.0 + Vector2(-orient.y, orient.x) * 45.0
    def gunpoint_right(self):
        orient = self.orientation()
        return self.sprite.position + orient * 10.0 - Vector2(-orient.y, orient.x) * 45.0
    def orientation(self):
        return self.sprite.get_local_transform() * Vector2(0,1)
    def make_shots(self):
        rv = []
        for gunpoint in [self.gunpoint_left, self.gunpoint_right, self.gunpoint]:
            shot = LaserShot( "laserGreen.png", gunpoint(), self.body.velocity + self.orientation() * 1000, self.sprite.rotation )
            shot.do( Delay( 2.0 ) + KillAction(shot) )
            rv.append( shot )
        return rv

class ShipLayer ( cocos.layer.Layer ):
    is_event_handler = True

    def __init__(self, space):
        super( ShipLayer, self ).__init__()
        self.space = space
        self.ship = AtomicShip()
        self.tracking = None
        create_convex_polygon_object( self.ship, "player.png", (0,0), 0.0, ((98,48),(59,0),(41,0),(2,48),(44,72),(55,72)), 1.0 )
        self.ship.body.moment = pymunk.inf
#        create_disk_object( self.ship, "player.png", (0,0), 0.0, 50.0, 1.0 )
        self.keyboard_state = key.KeyStateHandler()
        self.acceleration = 10
        self.velocity = Vector2(0,0)
        self.things = []
        self.add( self.ship.sprite )
        self.things.append( self.ship )
        self.space.add( self.ship.body, self.ship.shape )
        for i in range(20):
            debris = Thing()
            debris.name = "Asteroid"
            pos = (random.random() - 0.5) * 2000, (random.random() - 0.5) * 2000
            d = random.random() * 2 * math.pi
            s = random.random() * 20.0
            vel = s * math.cos( d ), s * math.sin( d )
            rot = random.random() * 360
            create_convex_polygon_object( debris, "meteorBig.png", pos, rot, ((134,87),(129,39),(83,0),(24,14),(0,48),(14,84),(83,111)), 5.0 )
#            create_convex_polygon_object( debris, "meteorBig.png", pos, rot, ((50,50),(50,-50),(-50,-50),(-50,50)), 1.0 )
#            create_disk_object( debris, "meteorBig.png", pos, rot, 50, 1.0 )
            debris.body.velocity = vel
            self.add( debris.sprite )
            self.things.append( debris )
            self.space.add( debris.body, debris.shape )
    def on_key_press(self, symbol, modifiers):
        if symbol == key.SPACE:
            for shot in self.ship.make_shots():
                self.projectile.add( shot )
        else:
            self.keyboard_state.on_key_press( symbol, modifiers )
    def on_key_release(self, symbol, modifiers):
        self.keyboard_state.on_key_release( symbol, modifiers )
    def on_mouse_motion(self, x, y, dx, dy):
        xy = cocos.director.director.get_virtual_coordinates( x, y )
        xy = (x - self.position[0], y - self.position[1])
#        for thing in self.things:
#            print thing, thing.sprite.position
        things = [shape.thing for shape in self.space.point_query( xy ) ]
        if things:
            self.tracking = things[0]
        else:
            self.tracking = None
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
