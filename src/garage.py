import graphics
import blocks
import cocos

from world import World
from game import create_ship_thing

class GarageWorld (World):
    def __init__(self, resolution = (1000,800), **kwargs):
        super( GarageWorld, self ).__init__( **kwargs )
        self.window = graphics.Window( (1000,800) )
        self.scene = graphics.Scene( self.window )
        self.main_layer = graphics.Layer( self.scene )
        self.root_node = cocos.cocosnode.CocosNode()
        self.main_layer.cocos_layer.add( self.root_node )
        root = blocks.OctaBlock(32)
        root.rotate_degrees(90)
        self.root_node.scale = 1
        s = blocks.BlockStructure( root )
        for i in range(7):
            a = s.attach((0,i), blocks.QuadBlock(32), 0)
            b = s.attach((a,2), blocks.QuadBlock(32), 0)
            c = s.attach((b,2), blocks.QuadBlock(32), 0)
            d = s.attach((c,1), blocks.QuadBlock(32), 3)
        self.block_structure = s
        self.sprite_structure = s.create_sprite_structure( cocos_parent = self.root_node )
    def run(self):
        self.window.run( self.scene )

if __name__ == '__main__':
    GarageWorld().run()
