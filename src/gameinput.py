import cocos

from pyglet.window import key

class CocosInputLayer ( cocos.layer.Layer ):
    is_event_handler = True

    def __init__(self):
        super( CocosInputLayer, self ).__init__()
        self.keyboard_state = key.KeyStateHandler()
        self.key_press_hooks = {}
        self.key_release_hooks = {}
        self.mouse_motion_hooks = []

    def on_key_press(self, symbol, modifiers):
        self.keyboard_state.on_key_press( symbol, modifiers )
        try:
            f = self.key_press_hooks[ symbol ]
        except:
            f = None
        if f:
            f( symbol, modifiers, self.keyboard_state )

    def on_key_release(self, symbol, modifiers):
        self.keyboard_state.on_key_release( symbol, modifiers )
        try:
            f = self.key_release_hooks[ symbol ]
        except:
            f = None
        if f:
            f( symbol, modifiers, self.keyboard_state )

    def on_mouse_motion(self, x, y, dx, dy):
        for hook in self.mouse_motion_hooks:
            hook( x, y, dx, dy )

    def set_key_press_hook( self, key, f ):
        self.key_press_hooks[ key ] = f

    def set_key_release_hook( self, key, f ):
        self.key_release_hooks[ key ] = f

    def set_key_hook( self, key, f ):
        self.key_press_hooks[ key ] = f
        self.key_release_hooks[ key ] = f
