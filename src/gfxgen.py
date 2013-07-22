import Image
import random
import math

from random import randint
from functools import partial
from itertools import starmap,product

from pymunk import Vec2d
from util import *
from geometry import *

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

def generate_starfields_main():
    size = 1024
    img, ar = create_new_image( size, size )
    for i in range(20):
        alph = random.random()
        on_hybrid_star( rand(1024), rand(1024), rand(32)+1, random.random() * 0.3 + 0.1, lambda xy, a : put_pixel_intensity(ar, (220+rand(35),220+rand(35),rand(35)), xy, a * min( 1.0, alph * 2 ) ) )
    img.save( "my_image.generated.png" )

def generate_simple_polygon(n = 3, size = 256, side_length = 0.3):
    vs = map(lambda p : (Vec2d(p)+Vec2d(1,1)*0.5)*size, generate_regular_polygon_vertices(n, radius_for_side_length(n, side_length)) )
    print vs
    img, ar = create_new_image( size, size )
    for x in range(size):
        for y in range(size):
            ar[x,y] = (200,100,100,255) if inside_convex_polygon( (x,y), vs ) else (100,200,50,255)
    img.save( "polygon_test.{0}.generated.png".format(n) )

def generate_fancy_polygon(n = 3, size = 256, side_length = 0.3, subpixel_resolution = 10):
    outer_r = radius_for_side_length(n, side_length)
    inner_r = outer_r - side_length/3.0
    print outer_r, inner_r, side_length
    outer_vs = map(Vec2d,generate_regular_polygon_vertices(n, outer_r))
    inner_vs = map(Vec2d,generate_regular_polygon_vertices(n, inner_r))
    print outer_vs, [ x.normalized() for x in outer_vs ]
    print inner_vs, [ x.normalized() for x in inner_vs ]
    polygons = []
    light_angle = 0.12345678 # unlikely for two angles to have exactly equal dot product
    light_direction = Vec2d(math.cos(light_angle), math.sin(light_angle))
    for ((a,b),(d,c)) in closed_circle_pairs( zip(inner_vs, outer_vs) ):
        print (a,b,c,d)
        t = ((a+b+c+d).normalized().dot( light_direction ) + 1) * 0.5
        t2 = 0.1 + 0.8 * t
        polygons.append( ((a,b,c,d),t2) ) 
    print inner_vs
    polygons.append( (inner_vs, 0.7512345) )
    print map( lambda x: x[1], polygons )
    def average( rgbas ):   
        rs, gs, bs, alphas = [], [], [], []
        for r, g, b, a in rgbas:
            if r != None: rs.append( r )
            if g != None: gs.append( g )
            if b != None: bs.append( b )
            if a != None: alphas.append( a )
        r = sum(rs) / float(len(rs)) if rs else 0.0
        g = sum(gs) / float(len(gs)) if gs else 0.0
        b = sum(bs) / float(len(bs)) if bs else 0.0
        a = sum(alphas) / float(len(alphas)) if alphas else 0.0
        return int(r), int(g), int(b), int(a)
    def sample( p ):
        p = (p - Vec2d(size,size)*0.5) / size
        for polygon, shade in polygons:
            if inside_convex_polygon( p, polygon ):
                return (shade*255,shade*255,shade*255,255)
        return (None,None,None,0) # transparent
        return (0,0,0,255) # solid black (not transparent -- that's None, None, None, 0)
    img, ar = create_new_image( size, size )
    print "generating fancy {0}-gon".format(n)
    for x, y in product( range(size), repeat = 2 ):
        print x, y
        results = []
        for sx, sy in product( [i/float(subpixel_resolution) for i in range(subpixel_resolution)], repeat = 2):
            p = (x + sx, y + sy)
            rv = sample(p)
            results.append( rv )
        result = average( results )
        ar[x,y] = result
    img.save( "polygon_fancy.{0}.generated.png".format(n) )
            
if __name__ == '__main__':
    for i in (4,6,5,8,3):
        generate_fancy_polygon(i, size = 256, side_length = 0.3)
    
