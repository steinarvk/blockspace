import graphics
import blocks
import cocos
import gameinput
import physics

from blocks import PolygonBlock

from world import World
from gameinput import key, mouse
from game import create_ship_thing

from util import *

from ship import Ship

class GarageWorld (World):
    def __init__(self, resolution = (1000,800), **kwargs):
        super( GarageWorld, self ).__init__( **kwargs )
        self.window = graphics.Window( (1000,800) )
        self.scene = graphics.Scene( self.window )
        self.sim = physics.PhysicsSimulator( timestep = None )
        self.input_layer = gameinput.CocosInputLayer()
        graphics.Layer( self.scene, self.input_layer )
        self.input_layer.mouse_motion_hooks.append( self.on_mouse_motion )
        self.main_layer = graphics.Layer( self.scene )
        self.root_node = cocos.cocosnode.CocosNode()
        self.main_layer.cocos_layer.add( self.root_node )
        self.mouse_layer = graphics.Layer( self.scene )
        root = PolygonBlock.load_file( "blocks/poly5.yaml" )
        self.root_node.scale = 1
#        for i in range(7):
#            a = s.attach((0,i), blocks.QuadBlock(32), 0)
#            b = s.attach((a,2), blocks.QuadBlock(32), 0)
#            c = s.attach((b,2), blocks.QuadBlock(32), 0)
#            d = s.attach((c,1), blocks.QuadBlock(32), 3)
#        self.sprite_structure = None
        self.garage_ship = None
        self.block_shapes = map( lambda n : (lambda : PolygonBlock.load_file( "blocks/poly{}.yaml".format(n) )), (3,4,5,6,8) )
        self.current_block_shape = self.block_shapes[0]
        self.restart_block_structure()
        self.mouse_sprite = self.current_block_shape().create_sprite()
        self.mouse_layer.cocos_layer.add( self.mouse_sprite )
        self.input_layer.mouse_scroll_hooks.add_anonymous_hook( self.on_mouse_scroll )
        self.input_layer.set_key_press_hook( key.SPACE, self.on_place_block )
        self.input_layer.set_key_press_hook( key.UP, self.on_next_shape )
        self.input_layer.set_key_press_hook( key.DOWN, self.on_previous_shape )
        self.input_layer.set_key_press_hook( key.R, self.on_restart_with_current )
        self.input_layer.mouse_press_hooks[ mouse.RIGHT ] = self.on_next_shape
        self.input_layer.mouse_press_hooks[ mouse.LEFT ] = self.on_place_block
        self.current_rotation = 0.0
        self.current_position = (0,0)
        self.refresh_garage_ship()
        self.physics.add_anonymous_hook( self.sim.tick )
        self.idle_time = 0.0
        self.currently_idle = False
    def on_restart_with_current(self, *args):
        self.reset_idle_time()
        self.restart_block_structure()
    def restart_block_structure(self, root = None):
        if not root:
            root = self.current_block_shape()
        self.block_structure = blocks.BlockStructure( root )
        self.refresh_garage_ship()
        
    def refresh_garage_ship(self):
        self.block_structure.zero_centroid()
        if self.garage_ship:
            self.garage_ship.kill()
        self.garage_ship = Ship( self, self.block_structure, (0,0), cocos_parent = self.root_node )
        self.pre_physics.add_hook( self.garage_ship, self.garage_ship.update )
        self.scene.schedule( self.update_everything )
    def start_idle_animation(self):
        self.currently_idle = True
        self.garage_ship.body.angular_velocity = 1.1
        # how come angular velocity below 1 radian fails?
    def stop_idle_animation(self):
        self.garage_ship.body.angular_velocity = 0
        self.garage_ship.body.angle = 0
        self.currently_idle = False
    def update_everything(self, dt):
        self.tick( dt )
        self.display_update()
        if not self.currently_idle:
            self.idle_time += dt
            if self.idle_time > 5.0:
                self.start_idle_animation()
    def reset_idle_time(self):
        self.idle_time = 0.0
        if self.currently_idle:
            self.stop_idle_animation()
    def on_place_block(self, *args):
        self.reset_idle_time()
        args = self.check_borders()
        if args:
            self.attach_current_block( *args )
    def check_borders(self):
        block = self.current_block_shape()
        block.rotate_degrees( -self.current_rotation )
        block.translate( self.current_position )
        for index in self.block_structure.free_edge_indices:
            edge = self.block_structure.edge( index )
        for local_edge_index in block.free_edge_indices:
            local_edge = block.edge( local_edge_index )
            for index in self.block_structure.free_edge_indices:
                edge = self.block_structure.edge( index )
                if local_edge.almost_overlaps( edge, max_distance = 5 ):
                    return (local_edge_index, index)
        return None
    def attach_current_block(self, current_block_edge_index, structure_edge_index ):
        block = self.current_block_shape()
        self.block_structure.attach( structure_edge_index, block, current_block_edge_index )
        self.refresh_garage_ship()
    def set_block_shape(self, shape):
        self.current_block_shape = shape
        p = self.mouse_sprite.position
        if self.mouse_sprite:
            self.mouse_sprite.kill()
        self.mouse_sprite = self.current_block_shape().create_sprite()
        self.mouse_sprite.rotation = self.current_rotation
        self.mouse_sprite.position = p
        self.mouse_layer.cocos_layer.add( self.mouse_sprite )
    def change_block_shape(self, delta = 1):
        self.set_block_shape(self.block_shapes[ (self.block_shapes.index( self.current_block_shape ) + delta) % len( self.block_shapes )])
    def on_next_shape(self, *args):
        self.reset_idle_time()
        self.change_block_shape( 1 )
    def on_previous_shape(self, *args):
        self.reset_idle_time()
        self.change_block_shape( -1 )
    def rotate_sprite(self, taps = 1):
        self.current_rotation = (self.current_rotation + taps * 10) % 360.0
        self.mouse_sprite.rotation = self.current_rotation
    def on_mouse_scroll(self, x, y, sx, sy):
        self.reset_idle_time()
        self.rotate_sprite( sy )
    def on_mouse_motion(self, x, y, dx, dy):
        self.reset_idle_time()
        self.current_position = self.root_node.point_to_local( (x,y) )
        self.mouse_sprite.position = self.current_position
    def run(self):
        self.window.run( self.scene )

if __name__ == '__main__':
    GarageWorld().run()
