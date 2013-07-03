import Image
import random

from random import randint
from functools import partial

def rand(n):
    return random.randint(0, n - 1)

def create_new_image( w, h ):
    img = Image.new( "RGBA", (w,h) )
    ar = img.load()
    width, height = img.size
    class Accessor:
        def __getitem__(self, indices):
            x, y = indices
            return ar[ x % width, y % height ]
        def __setitem__(self, indices, value):
            x, y = indices
            ar[ x % width, y % height ] = value
    return img, Accessor()

def on_disk( cx, cy, r, f ):
    u = int(r) + 1
    for dx in range(-u,u+1):
        for dy in range(-u,u+1):
            if (dx*dx + dy*dy) <= (r*r):
                f( (cx+dx, cy+dy) )

def on_square_star( cx, cy, r, n, f ):
    u = int(r) + 1
    for dx in range(-u,u+1):
        for dy in range(-u,u+1):
            y = (abs(dx)**n + abs(dy)**n) / r**n
            if y <= 1:
                f( (cx+dx, cy+dy), 1 - y )
    
def put_pixel( o, col, xy ):
    o[ xy ] = col

def put_pixel_intensity( o, col, xy, a ):
    if isinstance(a, float):
        a = int(255*a)
    r, g, b = col
    o[ xy ] = (r,g,b,a)

if __name__ == '__main__':
    size = 1024
    img, ar = create_new_image( size, size )
    for i in range(100):
        on_square_star( rand(1024), rand(1024), rand(32)+1, random.random() * 0.3 + 0.1, lambda xy, a : put_pixel_intensity(ar, (220+rand(35),220+rand(35),rand(35)), xy, a * min( 1.0, random.random() * 2 ) ) )
    img.save( "my_image.generated.png" )

