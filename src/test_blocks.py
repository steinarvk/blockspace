from blocks import *
from util import almost_equal

def test_quad_block():
    for side in (16.0,17.5,32):
        q = QuadBlock( side )
        assert all( [ almost_equal(side, edge.length) for edge in q.edges ] )
        expected_angles = (0,90,180,270)
        for angle, expected_angle in zip(sorted([edge.angle_degrees for edge in q.edges]),expected_angles):
            assert almost_equal( angle, expected_angle )
        bottom_edge, right_edge, top_edge, left_edge = q.edges
        assert almost_equal(270, bottom_edge.angle_degrees)
        assert almost_equal(0, right_edge.angle_degrees)
        assert almost_equal(90, top_edge.angle_degrees)
        assert almost_equal(180, left_edge.angle_degrees)
        q.rotate_degrees( 45.0 )
        expected_angles = (45,135,225,315)
        for angle, expected_angle in zip(sorted([edge.angle_degrees for edge in q.edges]),expected_angles):
            assert almost_equal( angle, expected_angle )
