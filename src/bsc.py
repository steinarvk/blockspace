import sys
import time

def include_build_directory():
    sys.path.append( "./build/lib.linux-x86_64-2.7" )

if __name__ == '__main__':
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
#    psys.reserve( 20 )
#    psys.add( size = (0.4,0.4), texture_coordinates = (0.0,0.0), texture_size = (1.0,1.0), position = (0,0), offset = (0,0), angle = 0.0, colour = (255,255,255,255) )
    @window.event
    def on_draw():
        pyglet.gl.glClearColor( 0.5, 0.2, 0.5, 1.0 )
        window.clear()
        label.draw()
        dt = time.time() - t0
        psys.draw()# position = (dt,2*dt) )
        fps.draw()
    pyglet.app.run()
