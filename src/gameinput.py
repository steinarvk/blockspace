import cocos

from util import Hookable

from pyglet.window import key
from pyglet.window import mouse

class CocosInputLayer ( cocos.layer.Layer ):
    is_event_handler = True

    def __init__(self):
        super( CocosInputLayer, self ).__init__()
        self.keyboard_state = key.KeyStateHandler()
        self.key_press_hooks = {}
        self.key_release_hooks = {}
        self.mouse_motion_hooks = []
        self.mouse_scroll_hooks = Hookable()
        self.mouse_press_hooks = {}

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.mouse_scroll_hooks( x, y, scroll_x, scroll_y )

    def on_mouse_press(self, x, y, button, modifiers):
        try:
            f = self.mouse_press_hooks[button]
        except:
            f = None
        if f:
            f( x, y, button, modifiers)

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
