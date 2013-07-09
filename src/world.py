class Hookable (object):
    def __init__(self):
        self.hooks = {}
    def add_hook(self, obj, f ):
        try:
            self.hooks[ obj ].append( f )
        except KeyError:
            self.hooks[ obj ] = [ f ]
    def add_anonymous_hook(self, f ):
        self.add_hook( None, f )
    def remove_hooks(self, obj ):
        try:
            del self.hooks[ obj ]
        except KeyError:
            pass
    def __call__(self, *args, **kwargs):
        for hooks in self.hooks.values():
            for hook in hooks:
                hook(*args, **kwargs)

class World (object):
    def __init__(self):
        self.hookpoints = []
        self.pre_physics = Hookable()
        self.hookpoints.append( self.pre_physics )
        self.physics = Hookable()
        self.hookpoints.append( self.physics )
        self.post_physics = Hookable()
        self.hookpoints.append( self.post_physics )
        self.pre_display = Hookable()
        self.hookpoints.append( self.pre_display )
        self.display = Hookable()
        self.hookpoints.append( self.display )
    def fixed_tick(self, dt):
        self.pre_physics( dt )
        self.physics( dt )
        self.post_physics( dt )
    def remove_all_hooks(self, obj):
        for hookable in self.hookpoints:
            hookable.remove_hooks( obj )
    def display_update(self):
        self.pre_display()
        self.display()