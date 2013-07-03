import Image
import random
import math

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

def on_hybrid_star( cx, cy, r, n, f ):
    u = int(r) + 1
    for dx in range(-u,u+1):
        for dy in range(-u,u+1):
            z = math.sqrt(dx*dx + dy*dy) / float(r)
            y = (abs(dx)**n + abs(dy)**n) / float(r**n)
            zy = ( z * (y**19) ) ** (1.0 / 20.0)
            if zy <= 1:
                f( (cx+dx, cy+dy), 1 - zy )
    
def put_pixel( o, col, xy ):
    o[ xy ] = col

def blend( rgba0, rgba1 ):
    r0,g0,b0,a0 = rgba0
    r1,g1,b1,a1 = rgba1
    if (a0 + a1) == 0:
        return 0, 0, 0, 0
    p = (a1/(a0+a1))
    r = r1 * p + r0 * (1.0-p)
    g = g1 * p + g0 * (1.0-p)
    b = b1 * p + b0 * (1.0-p)
    return r1,g1,b1,a1

def put_pixel_intensity( o, col, xy, a ):
    a = int(255*a)
    r, g, b = col
    o[ xy ] = blend( o[xy], (r,g,b,a) )

if __name__ == '__main__':
    size = 1024
    img, ar = create_new_image( size, size )
    for i in range(20):
        alph = random.random()
        on_hybrid_star( rand(1024), rand(1024), rand(32)+1, random.random() * 0.3 + 0.1, lambda xy, a : put_pixel_intensity(ar, (220+rand(35),220+rand(35),rand(35)), xy, a * min( 1.0, alph * 2 ) ) )
    img.save( "my_image.generated.png" )

