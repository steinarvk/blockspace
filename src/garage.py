import graphics
import blocks
import cocos
import gameinput

from world import World
from gameinput import key
from game import create_ship_thing

from util import *

class GarageWorld (World):
    def __init__(self, resolution = (1000,800), **kwargs):
        super( GarageWorld, self ).__init__( **kwargs )
        self.window = graphics.Window( (1000,800) )
        self.scene = graphics.Scene( self.window )
        self.input_layer = gameinput.CocosInputLayer()
        graphics.Layer( self.scene, self.input_layer )
        self.input_layer.mouse_motion_hooks.append( self.on_mouse_motion )
        self.main_layer = graphics.Layer( self.scene )
        self.root_node = cocos.cocosnode.CocosNode()
        self.main_layer.cocos_layer.add( self.root_node )
        self.mouse_layer = graphics.Layer( self.scene )
        root = blocks.OctaBlock(32)
        root.rotate_degrees(90)
        self.root_node.scale = 1
        s = blocks.BlockStructure( root )
#        for i in range(7):
#            a = s.attach((0,i), blocks.QuadBlock(32), 0)
#            b = s.attach((a,2), blocks.QuadBlock(32), 0)
#            c = s.attach((b,2), blocks.QuadBlock(32), 0)
#            d = s.attach((c,1), blocks.QuadBlock(32), 3)
        self.block_structure = s
        self.sprite_structure = None
        self.mouse_sprite = blocks.QuadBlock(32).create_sprite()
        self.mouse_layer.cocos_layer.add( self.mouse_sprite )
        self.input_layer.mouse_scroll_hooks.add_anonymous_hook( self.on_mouse_scroll )
        self.input_layer.set_key_press_hook( key.SPACE, self.on_place_block )
        self.current_rotation = 0.0
        self.current_position = (0,0)
        self.block_shapes = [ blocks.QuadBlock, blocks.OctaBlock ]
        self.current_block_shape = blocks.QuadBlock
        self.refresh_garage_ship()
    def refresh_garage_ship(self):
        self.block_structure.zero_centroid()
        if self.sprite_structure:
            self.sprite_structure.kill()
        self.sprite_structure = self.block_structure.create_sprite_structure( cocos_parent = self.root_node )
    def on_place_block(self, *args):
        args = self.check_borders()
        if args:
            self.attach_current_block( *args )
    def check_borders(self):
        block = self.current_block_shape(32)
        block.rotate_degrees( self.current_rotation )
        block.translate( self.current_position )
        for local_edge_index in block.free_edge_indices:
            local_edge = block.edge( local_edge_index )
            for index in self.block_structure.free_edge_indices:
                edge = self.block_structure.edge( index )
                if local_edge.almost_overlaps( edge, max_distance = 5 ):
                    return (local_edge_index, index)
        return None
    def attach_current_block(self, current_block_edge_index, structure_edge_index ):
        block = self.current_block_shape(32)
        self.block_structure.attach( structure_edge_index, block, current_block_edge_index )
        self.refresh_garage_ship()
    def set_block_shape(self, shape):
        self.current_block_shape = shape
        if self.mouse_sprite:
            self.mouse_sprite.kill()
        self.mouse_sprite = self.current_block_shape(32).create_sprite()
        self.mouse_sprite.rotation = self.current_rotation
        self.mouse_layer.cocos_layer.add( self.mouse_sprite )
    def change_block_shape(self):
        self.set_block_shape(self.block_shapes[ (self.block_shapes.index( self.current_block_shape ) + 1) % len( self.block_shapes )])
    def rotate_sprite(self, taps = 1):
        self.current_rotation = (self.current_rotation + taps * 10) % 360.0
        self.mouse_sprite.rotation = self.current_rotation
    def on_mouse_scroll(self, x, y, sx, sy):
        self.rotate_sprite( sy )
    def on_mouse_motion(self, x, y, dx, dy):
        self.current_position = self.root_node.point_to_local( (x,y) )
        self.mouse_sprite.position = self.current_position
    def run(self):
        self.window.run( self.scene )

if __name__ == '__main__':
    GarageWorld().run()
