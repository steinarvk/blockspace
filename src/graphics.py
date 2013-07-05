import cocos

from operator import attrgetter
from pyglet.gl import *

def update_sprite( thing ):
    thing.sprite.update()

def kill_sprite( thing ):
    thing.sprite.kill()

class Window (object):
    def __init__(self, size = (1024,768) ):
        self.width, self.height = size
        self.director = cocos.director.director
        self.director.init( width = self.width, height = self.height )
        self.director.show_FPS = True
    def run(self, scene):
        scene.finalize()
        self.director.run( scene.cocos_scene )
    def center(self):
        return 0.5 * self.width, 0.5 * self.height

class Scene (object):
    def __init__(self, window):
        self.layers = []
        self.window = window
        self.to_schedule = []
        self.update_hooks = []
        self.finalized = False
    def add_layer(self, layer):
        assert not self.finalized
        if isinstance( self, cocos.layer.Layer ):
            layer = Layer( layer )
        self.layers.append( layer )
    def finalize(self):
        cocos_layers = map( attrgetter("cocos_layer"), self.layers )
        self.cocos_scene = cocos.scene.Scene( *cocos_layers )
        for f in self.to_schedule:
            self.cocos_scene.schedule( f )
        self.finalized = True
    def schedule(self, f):
        self.to_schedule.append( f )
    def update(self):
        for layer in self.layers:
            layer.update()

class Layer (object):
    def __init__(self, scene, cocos_layer = None):
        self.scene = scene
        self.cocos_layer = cocos_layer or cocos.layer.Layer()
        self.sprites = set()
        self.cocos_layer.position = self.scene.window.center()
        self.camera = None
        scene.add_layer( self )
    def add_sprite(self, sprite):
        self.sprites.add( sprite )
    def remove_sprite(self, sprite):
        self.sprites.remove( sprite )
    def update(self):
        for sprite in self.sprites:
            sprite.update()
        if self.camera:
            self.cocos_layer.position = self.camera.offset()
        

class Sprite (object):
    def __init__(self, filename, thing, layer):
        self.cocos_sprite = cocos.sprite.Sprite( filename )
        self.cocos_sprite.anchor = (0,0)
        self.layer = layer
        self.thing = thing
        thing.sprite = self
        thing.kill_hooks.append( kill_sprite )
        thing.update_hooks.append( update_sprite )
        self.layer.cocos_layer.add( self.cocos_sprite )
        self.layer.add_sprite( self )
    def kill(self):
        self.layer.remove_sprite( self )
        self.layer.cocos_layer.remove( self.cocos_sprite )
    def update(self):
        self.cocos_sprite.position = self.thing.position
        self.cocos_sprite.rotation = self.thing.angle_degrees

class Camera (object):
    def __init__(self, window, focus = (0,0)):
        self.window = window
        self.focus = focus
        self.following = None
        self.tracking_inertia = 0.06

    def offset(self):
        x, y = self.focus
        return 0.5 * self.window.width - x, 0.5 * self.window.height - y

    def update(self, dt):
        if self.following:
            tx, ty = self.following.position
            ox, oy = self.focus
            p = self.tracking_inertia**dt
            self.focus = (p*ox + (1-p)*tx, p * oy + (1-p) * ty)


class BackgroundCocosLayer (cocos.layer.Layer):
    def __init__(self, camera, distance, image):
        super( cocos.layer.Layer, self ).__init__()
        self._camera = camera
        self._distance = distance
        self._image = pyglet.image.load( image )
        self._texture = self._image.get_texture()
        glBindTexture( self._texture.target, self._texture.id )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        self._k = 0.5 ** self._distance
    def draw(self):
        w, h = self._camera.window.width, self._camera.window.height
        s = max( w, h )
        hw = -(w+1)//2
        hh = -(h+1)//2
        x, y = self._camera.focus
        rx, ry = self._k * x, self._k * y
        glEnable( self._texture.target )
#        glColor4f( 0.3, 0.3, 0.3, 0.5 ) 
        glBindTexture( GL_TEXTURE_2D, self._texture.id )
        glPushMatrix()
        self.transform()
        glBegin( GL_QUADS )
        glTexCoord2f( rx, ry )
        glVertex2i( hw, hh )
        glTexCoord2f( rx + 1, ry )
        glVertex2i( hw + s, hh )
        glTexCoord2f( rx + 1, ry + 1 )
        glVertex2i( hw + s, hh + s )
        glTexCoord2f( rx, ry + 1 )
        glVertex2i( hw, hh + s )
        glEnd()
        glPopMatrix()

        
        

# thing = Thing( sim, ConvexPolygonShape((1,0),(0,1),(-1,0)) )
# VisualThing( "spaceship.png", thing, layer )


def draw_thing_shapes( thing ):
    glPushMatrix()
    thing.sprite.cocos_sprite.transform()
    glBegin( GL_TRIANGLES )
    for a, b, c in thing.abstract_shape.triangulate():
        glVertex2f( *a )
        glVertex2f( *b )
        glVertex2f( *c )
    glEnd()
    glPopMatrix()
