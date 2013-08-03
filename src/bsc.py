import sys
import time
import random
import math
from atlas import Atlas
from physics import Vec2d

def include_build_directory():
    sys.path.append( "./build/lib.linux-x86_64-2.7" )

def main():
    include_build_directory()
    import pyglet
    import pyglet.gl
    import bsgl
    import sys
    window = pyglet.window.Window( vsync = True, width = 1300, height = 1000)
    print window.width, window.height
    label = pyglet.text.Label( "Hello world!", font_name = "Times New Roman", font_size = 36, x = window.width//2, y = window.height//2, anchor_x = "center", anchor_y = "center" )
    atlas = Atlas( "atlas.generated" )
    tex = atlas.sheet.get_texture()
    fps = pyglet.clock.ClockDisplay()
    pyglet.clock.schedule( lambda _ : None )
    t0 = [time.time(), time.time()]
    psys = bsgl.System( texture_id = tex.id )
    print psys.get_capacity(), psys.get_number_of_elements()
    amount = 1000
    psys.reserve( amount )
    things = {}
    def add_things():
        for i in range( amount ):
            z = random.random() * 6.28
            r = 0.001 + random.random() * 0.01
            pos = r*math.cos(z), r*math.sin(z)
            vel = tuple(Vec2d( pos ).normalized()*(1+4*random.random())*3)
            offset = 0,0
            texcoords = 0,0
            texsize = 1,1
            angle = random.random() * 6.28
            avel = (-1 if random.random() > 0.5 else 1) * (random.random()*0.1+0.9) * 10 * Vec2d(vel).get_length()
            size = (0.1,0.1)
            rgba = [ random.random() for i in range(3) ] + [ 1.0 ]
            name = "polygon_normals.{}.generated".format( random.choice( (3,4,5,6,8) ) )
            rv = psys.add( size = size, texture_coordinates = atlas.texcoords(name), texture_size = atlas.texsize(name), position = pos, offset = offset, angle = angle, colour = rgba )
            things[ rv ] = (pos, angle, vel,avel)
    def update_things( dt ):
        for index, (pos, a, vel, avel) in things.items():
            x, y = pos
            dx, dy = vel
            t = 0.2 * dt
            xp, yp = x + t * dx, y + t * dy
            ap = a + t * avel
            things[index] = ((xp,yp),ap,vel,avel)
            psys.update_position_and_angle( index, (xp,yp), ap )
    def reset_things():
        for index in things.keys():
            del things[index]
            psys.remove( index )
        assert len(things) == 0
        add_things()
    add_things()
    indices = things.keys()
    add_things()
    for index in indices:
        psys.remove( index )
        del things[index]
    print psys.get_capacity(), psys.get_number_of_elements()
    @window.event
    def on_draw():
        pyglet.gl.glClearColor( 0.5, 0.2, 0.5, 1.0 )
        window.clear()
        label.draw()
        t1 = time.time()
        dt = t1 - t0[0]
        t0[0] = t1
        if (t1 - t0[1]) > 3.0:
            reset_things()
            t0[1] = t1
        update_things( dt )
        psys.draw()# position = (dt,2*dt) )
        fps.draw()
    pyglet.app.run()

if __name__ == '__main__':
    main()
