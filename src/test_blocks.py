from blocks import *
from util import almost_equal, degrees_almost_equal, vectors_almost_equal
import physics

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
        q.rotate_degrees( 11.0 )
        expected_angles = (56,146,236,326)
        for angle, expected_angle in zip(sorted([edge.angle_degrees for edge in q.edges]),expected_angles):
            assert almost_equal( angle, expected_angle )
        assert q.free_edge_indices == [0,1,2,3]

def test_quad_block_to_shape():
    for side in (16.0,17.5,32):
        q = QuadBlock( side )
        vs = q.vertices
        shape = q.create_collision_shape()
        assert isinstance( shape, physics.ConvexPolygonShape )
        for a, b in zip( q.vertices, shape.vertices ):
            assert vectors_almost_equal( a, b )
        assert almost_equal( shape.area(), side * side )

def test_attach_two_blocks():
    for angle in (0.0,23.0,45.0,72.0,123.0):
        a = QuadBlock(1)
        b = QuadBlock(1)
        a.rotate_degrees( angle )
        assert a.free_edge_indices == [0,1,2,3]
        assert b.free_edge_indices == [0,1,2,3]
        s = BlockStructure(a)
        assert len( s.free_edge_indices ) == 4
        s.attach((0,0), b, 0)
        assert len(s.blocks) == 2
        assert len(s.blocks[0].free_edge_indices) == 3
        assert len(s.blocks[1].free_edge_indices) == 3
        assert degrees_almost_equal( s.blocks[0].edges[0].angle_degrees, 270.0 + angle )
        [index1] = s.blocks[0].connections.values()
        [index2] = s.blocks[1].connections.values()
        assert degrees_almost_equal( s.edge(index1).angle_degrees, s.edge(index2).angle_degrees + 180.0 )
        assert len( s.free_edge_indices ) == 6


def test_attach_four_blocks_in_square():
    #  2  1
    # 3a12c0
    #  0  3
    #  1  3
    # 2b00d2
    #  3  1
    a = QuadBlock(1)
    b = QuadBlock(1)
    c = QuadBlock(1)
    d = QuadBlock(1)
    s = BlockStructure(a)
    assert len( s.free_edge_indices ) == 4
    assert degrees_almost_equal( s.edge( (0,0) ).angle_degrees, 270.0 )
    a_index = 0
    assert vectors_almost_equal( s.blocks[a_index].create_collision_shape().centroid(), (0,0) )
    b_index = s.attach((0,0), b, 1)
    assert vectors_almost_equal( s.blocks[b_index].create_collision_shape().centroid(), (0,-1) )
    assert len( s.free_edge_indices ) == 6
    assert degrees_almost_equal( s.edge( (b_index,1) ).angle_degrees, 90.0 )
    assert degrees_almost_equal( s.edge( (0,1) ).angle_degrees, 0.0 )
    c_index = s.attach((0,1), c, 2)
    assert vectors_almost_equal( s.blocks[c_index].create_collision_shape().centroid(), (1,0) )
    assert len( s.free_edge_indices ) == 8
    assert degrees_almost_equal( s.edge( (c_index,3) ).angle_degrees, 270.0 )
    d_index = s.attach((c_index,3), d, 3)
    assert vectors_almost_equal( s.blocks[d_index].create_collision_shape().centroid(), (1,-1) )
    assert degrees_almost_equal( s.edge( (d_index,3) ).angle_degrees, 90.0 )
    assert len( s.free_edge_indices ) == 8
    assert almost_equal( s.edge( (a_index,0) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (a_index,1) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (a_index,2) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (a_index,3) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (b_index,0) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (b_index,1) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (b_index,2) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (b_index,3) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (c_index,0) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (c_index,1) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (c_index,2) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (c_index,3) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (d_index,0) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (d_index,1) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (d_index,2) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (d_index,3) ).angle_degrees, 90 )

def test_attach_four_blocks_in_line():
    #  2  1  1  3
    # 3a12c02b00d2
    #  0  3  3  1
    a = QuadBlock(1)
    b = QuadBlock(1)
    c = QuadBlock(1)
    d = QuadBlock(1)
    s = BlockStructure(a)
    assert len( s.free_edge_indices ) == 4
    a_index = 0
    c_index = s.attach((a_index,1), c, 2)
    assert len( s.free_edge_indices ) == 6
    b_index = s.attach((c_index,0), b, 2)
    assert len( s.free_edge_indices ) == 8
    d_index = s.attach((b_index,0), d, 0)
    assert len( s.free_edge_indices ) == 10
    assert almost_equal( s.edge( (a_index,0) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (a_index,1) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (a_index,2) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (a_index,3) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (b_index,0) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (b_index,1) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (b_index,2) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (b_index,3) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (c_index,0) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (c_index,1) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (c_index,2) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (c_index,3) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (d_index,0) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (d_index,1) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (d_index,2) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (d_index,3) ).angle_degrees, 90 )

def test_attach_four_blocks_in_knightsmove():
    #  2  1  1 
    # 3a12c02b0
    #  0  3  3 
    #        1
    #       2d0
    #        3
    a = QuadBlock(1)
    b = QuadBlock(1)
    c = QuadBlock(1)
    d = QuadBlock(1)
    s = BlockStructure(a)
    assert len( s.free_edge_indices ) == 4
    a_index = 0
    c_index = s.attach((a_index,1), c, 2)
    assert len( s.free_edge_indices ) == 6
    b_index = s.attach((c_index,0), b, 2)
    assert len( s.free_edge_indices ) == 8
    d_index = s.attach((b_index,3), d, 1)
    assert len( s.free_edge_indices ) == 10
    assert almost_equal( s.edge( (a_index,0) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (a_index,1) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (a_index,2) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (a_index,3) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (b_index,0) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (b_index,1) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (b_index,2) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (b_index,3) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (c_index,0) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (c_index,1) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (c_index,2) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (c_index,3) ).angle_degrees, 270 )
    assert almost_equal( s.edge( (d_index,0) ).angle_degrees, 0 )
    assert almost_equal( s.edge( (d_index,1) ).angle_degrees, 90 )
    assert almost_equal( s.edge( (d_index,2) ).angle_degrees, 180 )
    assert almost_equal( s.edge( (d_index,3) ).angle_degrees, 270 )
