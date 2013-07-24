import cocos
import math

from util import ignore_arguments
from operator import attrgetter
from pyglet.gl import *

from weakref import WeakValueDictionary

MemoizedLoad = WeakValueDictionary()

def memoized_load( f, *args, **kwargs ):
    key = f, args, frozenset(kwargs.items())
    try:
        rv = MemoizedLoad[ key ]()
    except KeyError:
        rv = None
    if rv == None:
        rv = MemoizedLoad[ key ] = f(*args, **kwargs)
    return rv

def load_grid( fn, cols, rows ):
    image = pyglet.image.load( fn )
    return pyglet.image.ImageGrid( image, cols, rows )

def create_sprite( info ):
    if info.has_key( "image-name" ):
        image_name = info["image-name"]
        rv = cocos.sprite.Sprite( image_name )
    elif info.has_key( "grid-name" ):
        grid = memoized_load( load_grid, info["grid-name"], info["grid-columns"], info["grid-rows"] )
        image = grid[ info[ "index"] ]
        rv = cocos.sprite.Sprite( image )
    else:
        assert False
    colour = info.get( "colour", (255,255,255) )
    scale = info.get( "scale", 1.0 )
    rv.color = colour
    rv.scale = scale
    return rv

def create_label( x, y, text = "", size = 16, font_name = "Bitstream Vera Sans Mono", layer = None ):
    rv = cocos.text.Label( "", font_name = font_name, font_size = size, anchor_x = "left", anchor_y = "top" ) 
    rv.height = size
    rv.position = (x,y)
    rv.element.text = text
    if layer:
        layer.add( rv )
    return rv

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

class BlankingCocosLayer (cocos.layer.Layer):
    def __init__(self, *args, **kwargs):
        super(BlankingCocosLayer, self).__init__(*args, **kwargs)
        self.clear_rect = None
        self.clear_colour = None
    def draw(self):
        glPushMatrix()
        self.transform()
        if self.clear_rect:
            glColor4ub( *self.clear_colour )
            glBegin( GL_QUADS )
            for p in self.clear_rect:
                glVertex2i( *p )
            glEnd()
        glPopMatrix()
        super(BlankingCocosLayer, self).draw()

class Layer (object):
    def __init__(self, scene, cocos_layer = None):
        self.scene = scene
        self.cocos_layer = cocos_layer or cocos.layer.Layer()
        self.sprites = set()
        self.cocos_layer.position = self.scene.window.center()
        self.camera = None
        self.size = None
        scene.add_layer( self )
    def add_sprite(self, sprite):
        self.sprites.add( sprite )
    def remove_sprite(self, sprite):
        self.sprites.remove( sprite )
    def update(self):
        for sprite in self.sprites:
            sprite.update()
        if self.camera:
            self.cocos_layer.position = self.camera.offset( window_size = self.size )
        

class Sprite (object):
    def __init__(self, image, thing, layer = None):
        self.cocos_sprite = cocos.sprite.Sprite( image )
        self.layer = layer
        self.thing = thing
        thing.sprite = self
        thing.kill_hooks.append( kill_sprite )
        thing.update_hooks.append( update_sprite )
        if self.layer:
            self.layer.cocos_layer.add( self.cocos_sprite )
            self.layer.add_sprite( self )
    def kill(self):
        if self.layer:
            self.layer.remove_sprite( self )
            self.layer.cocos_layer.remove( self.cocos_sprite )
    def update(self):
        self.cocos_sprite.position = self.thing.position
        self.cocos_sprite.rotation = 180.0 - self.thing.angle_degrees

        
        


class SpriteStructure (object):
    def __init__(self, thing = None, layer = None, cocos_parent = None):
        self.layer = layer
        self.cocos_parent = cocos_parent
        self.cocos_sprites = []
        self.kill_hook = ignore_arguments( self.kill )
        self.update_hook = ignore_arguments( self.update )
        self.thing = None
        self.node = cocos.cocosnode.CocosNode()
        self.subcomponent = {}
        if self.layer:
            self.layer.add_sprite( self )
            self.layer.cocos_layer.add( self.node )
        if self.cocos_parent:
            self.cocos_parent.add( self.node )
        if thing:
            self.follow_thing( thing )
    def follow_thing(self, thing):
        self.thing = thing
        self.thing.kill_hooks.append( self.kill_hook )
        self.thing.update_hooks.append( self.update_hook )
    def add_sprite(self, sprite, offset = (0,0), key = None, rotation = 0.0, z = 0):
        cocos_sprite = sprite
        w, h = cocos_sprite.width, cocos_sprite.height
        cocos_sprite.position = offset
        cocos_sprite.rotation = rotation
        self.cocos_sprites.append( cocos_sprite )
        self.node.add( cocos_sprite, z = z )
        if key:
            self.subcomponent[key] = cocos_sprite
        return cocos_sprite
    def replace_sprite(self, old_sprite, new_sprite ):
        old_position = old_sprite.position
        cocos_sprite = new_sprite
        cocos_sprite.position = old_position
        self.node.remove( old_sprite )
        self.cocos_sprites.remove( old_sprite )
        self.node.add( cocos_sprite )
        self.cocos_sprites.append( cocos_sprite )
        return cocos_sprite
    def remove_sprite(self, cocos_sprite):
        self.cocos_sprites.remove( cocos_sprite )
        self.node.remove( cocos_sprite )
    def kill(self):
        if self.thing:
            self.thing.kill_hooks.remove( self.kill_hook )
            self.thing.update_hooks.remove( self.update_hook )
        if self.cocos_parent:
            self.cocos_parent.remove( self.node )
        if self.layer:
            self.layer.remove_sprite( self )
            self.layer.cocos_layer.remove( self.node )
    def update(self):
        if self.thing:
            p = self.thing.position
            r = - self.thing.angle_degrees
            self.node.position  = p
            self.node.rotation = r


class Camera (object):
    def __init__(self, window, focus = (0,0)):
        self.window = window
        self.focus = focus
        self.following = None
        self.tracking_inertia = 0.06

    def offset(self, window_size = None):
        x, y = self.focus
        if not window_size:
            window_size = self.window.width, self.window.height
        w, h = window_size
        return 0.5 * w - x, 0.5 * h - y

    def update(self, dt):
        if self.following:
            tx, ty = self.following.position
            ox, oy = self.focus
            p = self.tracking_inertia**dt
            self.focus = (p*ox + (1-p)*tx, p * oy + (1-p) * ty)

    @property
    def position(self):
        return self.focus

class VerticalBar (cocos.cocosnode.CocosNode):
    def __init__(self, width, height, on_colour, off_colour):
        super( VerticalBar, self ).__init__()
        self.on_colour = on_colour
        self.off_colour = off_colour
        self.width = width
        self.height = height
        self.fill = 0.75
    def draw(self):
        glPushMatrix()
        self.transform()
        glBegin( GL_QUADS )
        hh = self.fill * self.height
        w, h = float(self.width), float(self.height)
        glColor3ub( *self.off_colour )
        glVertex2f( 0.0, 0.0 )
        glVertex2f( w, 0.0 )
        glVertex2f( w, h )
        glVertex2f( 0.0, h )
        glColor3ub( *self.on_colour )
        glVertex2f( 0.0, 0.0 )
        glVertex2f( w, 0.0 )
        glVertex2f( w, hh )
        glVertex2f( 0.0, hh )
        glEnd()
        glPopMatrix()

class Minimap (cocos.cocosnode.CocosNode):
    def __init__(self, width, height, world_width, world_height, cam):
        super( Minimap, self ).__init__()
        import test_component
        self.width = width
        self.height = height
        self.world_width = world_width
        self.world_height = world_height
        self.batch = cocos.batch.BatchNode()
        self.batch.position = (self.width*0.5, self.height*0.5)
        self.batch.scale = 1
        self.add( self.batch )
        self.sprites = {}
        self.minimap_xscale = width / float(world_width)
        self.minimap_yscale = height / float(world_height)
        self.following = cam
    def add_sprite(self, thing, sprite):
        self.sprites[ thing ] = sprite
        self.batch.add( sprite )
    def remove_sprite(self, thing):
        sprite = self.sprites[ thing ]
        del self.sprites[ thing ]
        self.batch.remove( sprite )
    def update(self):
        cx, cy = self.following.position
        for thing, sprite in self.sprites.items():
            x, y = thing.position
            dx, dy = (x-cx)*self.minimap_xscale, (y-cy)*self.minimap_yscale
            sprite.position = dx, dy
    def visit(self):
        glEnable( GL_SCISSOR_TEST )
        x, y = self.position
        glScissor( x, y, self.width, self.height )
        super(Minimap, self).visit()
        glDisable( GL_SCISSOR_TEST )
    def draw(self):
        glPushMatrix()
        self.transform()
        glColor4ub( 0, 32, 0, 255 )
        glBegin( GL_QUADS )
        glVertex2i(0,0)
        glVertex2i(self.width,0)
        glVertex2i(self.width,self.height)
        glVertex2i(0,self.height)
        glEnd()
        glPopMatrix()


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
        glColor4f( 1, 1, 1, 1 )
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
    x, y = thing.position
    ax, ay = thing.centroid
    glColor4f( 1.0, 1.0, 1.0, 1.0 )
    glBegin( GL_TRIANGLES )
    for abc in thing.abstract_shape.triangulate():
        for dx, dy in abc:
            rdx, rdy = dx - ax, dy - ay
            ar = thing.angle_radians
#            cost, sint = math.cos(ar), math.sin(ar)
            cost, sint = 1, 0
            glVertex2f( x + rdx * cost - rdy * sint, y + rdx * sint + rdy * cost )
    glEnd()
    glPopMatrix()

def update_visible_objects( space, center_xy, size, all_objects, batch_node, sprite_key ):
    # TODO, be more consistent, make everything Things
    x, y = center_xy
    ww, wh = size
    hw, hh = 0.5 * ww, 0.5 * wh
    screen_slack = 100.0
    screen_bb = pymunk.BB(x-hw-screen_slack,y-hh-screen_slack,x+hw+screen_slack,y+hh+screen_slack)
    onscreen = set(space.bb_query( screen_bb ))
    for shape in onscreen:
        sprite_key(shape).update()
    prech = set(batch_node.get_children())
    for thing in all_things:
        if all((shape not in onscreen for shape in thing.shapes)):
            if spr.cocos_sprite in prech:
                batch_node.remove( spr.cocos_sprite )
        else:
            thing.update()
            if spr.cocos_sprite not in prech:
                batch_node.add( spr.cocos_sprite )
