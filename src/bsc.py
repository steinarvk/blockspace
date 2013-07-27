import sys
import time
import random

def include_build_directory():
    sys.path.append( "./build/lib.linux-x86_64-2.7" )

def main():
    include_build_directory()
    import pyglet
    import pyglet.gl
    import bsgl
    import sys
    window = pyglet.window.Window( vsync = False, width = 1300, height = 1000)
    print window.width, window.height
    label = pyglet.text.Label( "Hello world!", font_name = "Times New Roman", font_size = 36, x = window.width//2, y = window.height//2, anchor_x = "center", anchor_y = "center" )
    sheet = pyglet.image.load( "mynormaltriangle.png" )
    fps = pyglet.clock.ClockDisplay()
    pyglet.clock.schedule( lambda _ : None )
    t0 = time.time()
    psys = bsgl.System( texture_id = sheet.texture.id )
    print psys.get_capacity(), psys.get_number_of_elements()
    psys.reserve( 1000 )
    for i in range( 1000 ):
        pos = [ random.random() for i in range(2) ]
        offset = 0,0
        texcoords = 0,0
        texsize = 1,1
        angle = random.random() * 6.28
        size = (0.05,0.05)
        rgba = [ random.random() for i in range(3) ] + [ 1.0 ]
        psys.add( size = size, texture_coordinates = texcoords, texture_size = texsize, position = pos, offset = offset, angle = angle, colour = rgba )
    print psys.get_capacity(), psys.get_number_of_elements()
    @window.event
    def on_draw():
        pyglet.gl.glClearColor( 0.5, 0.2, 0.5, 1.0 )
        window.clear()
        label.draw()
        dt = time.time() - t0
        psys.draw()# position = (dt,2*dt) )
        fps.draw()
    pyglet.app.run()

if __name__ == '__main__':
    main()
