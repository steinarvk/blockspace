import random
import math

from util import *

def almost_equal( x, y ):
    k = 0.0001
    return abs( x - y ) <= k * min( abs(x), abs(y) )

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