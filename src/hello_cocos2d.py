import cocos
from cocos.actions import *

class HelloWorld ( cocos.layer.Layer ):
    is_event_handler = True

    def __init__(self):
        super( HelloWorld, self ).__init__()
        self.label = cocos.text.Label( "Hello world", font_name = "Times New Roman", font_size = 32, anchor_x = "center", anchor_y = "center" )
        self.label.position = 320,240
        self.label.do( Repeat( RotateBy(360, duration=10) ) )
        self.add( self.label )
    def on_mouse_motion(self, x, y, dx, dy):
        self.label.element.text = "Hello World {0} {1}".format( x, y )

if __name__ == '__main__':
    cocos.director.director.init()
    layer = HelloWorld()
    scene = cocos.scene.Scene( layer )
    cocos.director.director.run( scene )
