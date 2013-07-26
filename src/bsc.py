import sys
import time

def include_build_directory():
    sys.path.append( "./build/lib.linux-x86_64-2.7" )

if __name__ == '__main__':
    include_build_directory()
    import bsgl
    import pyglet
    window = pyglet.window.Window( vsync = False )
    label = pyglet.text.Label( "Hello world!", font_name = "Times New Roman", font_size = 36, x = window.width//2, y = window.height//2, anchor_x = "center", anchor_y = "center" )
    fps = pyglet.clock.ClockDisplay()
    pyglet.clock.schedule( lambda _ : None )
    t0 = time.time()
    psys = bsgl.System()
    @window.event
    def on_draw():
        window.clear()
        label.draw()
        fps.draw()
        psys.draw( window.width, window.height, time.time() - t0, 300, 200, 100 )
    pyglet.app.run()
