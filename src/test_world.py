from world import *
from functools import partial
from operator import add, sub, mul, div

def test_basic_hookable():
    x = [ 0 ]
    def foo( f, n ):
        x[0] = f( x[0], n )
    h = Hookable()
    h.add_anonymous_hook( partial(foo, add, 42 ) )
    assert x[0] == 0
    h()
    assert x[0] == 42
    h()
    assert x[0] == 84

def test_hookable_preserves_internal_order():
    x = [0]
    def foo( f, n ):
        x[0] = f( x[0], n )
    h = Hookable()
    h.add_anonymous_hook( partial(foo, add, 1 ) )
    h.add_anonymous_hook( partial(foo, mul, 2 ) )
    h.add_anonymous_hook( partial(foo, sub, 3 ) )
    assert x[0] == 0
    h()
    assert x[0] == -1
    h()
    assert x[0] == -3
    h()
    assert x[0] == -7

def test_world_hookables():
    x = []
    y = []
    def foo_dt( s, dt ):
        x.append( s.format( dt ) )
    def foo( s ):
        y.append( s )
    w = World()
    w.pre_physics.add_anonymous_hook( partial( foo_dt, "pre-physics 1 {0}" ) )
    w.pre_physics.add_anonymous_hook( partial( foo_dt, "pre-physics 2 {0}" ) )
    w.physics.add_anonymous_hook( partial( foo_dt, "physics 1 {0}" ) )
    w.physics.add_anonymous_hook( partial( foo_dt, "physics 2 {0}" ) )
    w.post_physics.add_anonymous_hook( partial( foo_dt, "post-physics 1 {0}" ) )
    w.post_physics.add_anonymous_hook( partial( foo_dt, "post-physics 2 {0}" ) )
    w.pre_display.add_anonymous_hook( partial( foo, "pre-display 1"))
    w.pre_display.add_anonymous_hook( partial( foo, "pre-display 2"))
    w.display.add_anonymous_hook( partial( foo, "display 1"))
    w.display.add_anonymous_hook( partial( foo, "display 2"))
    ex = []
    for n in (11,12):
        w.fixed_tick( n )
        ex.append( "pre-physics 1 {0}".format(n) ) 
        ex.append( "pre-physics 2 {0}".format(n) ) 
        ex.append( "physics 1 {0}".format(n) ) 
        ex.append( "physics 2 {0}".format(n) ) 
        ex.append( "post-physics 1 {0}".format(n) ) 
        ex.append( "post-physics 2 {0}".format(n) ) 
    assert x == ex
    assert y == []
    w.display_update()
    assert x == ex
    assert y == [ "pre-display 1", "pre-display 2", "display 1", "display 2" ]
