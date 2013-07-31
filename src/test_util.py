import random
import math

from util import *

def test_radians_to_degrees_and_back():
    for i in range(100):
        x = random.random() * 18 - 4
        deg = radians_to_degrees( x )
        rad = degrees_to_radians( deg )
        assert almost_equal( x % (math.pi * 2), rad % (math.pi * 2) )
        assert almost_equal( math.cos(x), math.cos(rad) )
        assert almost_equal( math.sin(x), math.sin(rad) )

def test_degrees_to_radians_and_back():
    for i in range(100):
        x = random.random() * 1000 - 360
        rad = degrees_to_radians( x )
        deg = radians_to_degrees( rad )
        assert almost_equal( x % 360.0, deg % 360.0 )

def test_almosts():
    for i in range(1000):
        x = (random.random() - 0.5) * 100000
        dx = 0.000000001
        assert almost_equal( x, x + dx )
        assert almost_equal( x, x - dx )
        assert almost_leq( x, x + dx )
        assert almost_geq( x + dx, x )
        assert almost_leq( x, x + abs(x) )
        assert not almost_geq( x, x + abs(x) )
        assert not almost_leq( x + abs(x), x )
        assert almost_geq( x + abs(x), x )

def test_radius_for_side_length():
    import math
    for i in range(1000):
        s = random.random() * 1000 + 0.1 
        a = random.random() * 6.28
        n = random.randint(3,20)
        da = (2*math.pi/float(n))
        r = radius_for_side_length( n, s )
        x1 = Vec2d(polar_radians( a, r ))
        x2 = Vec2d(polar_radians( a + da, r ))
        assert almost_equal( s, (x1-x2).get_length() )
