from blocks import *
from util import almost_equal, degrees_almost_equal, vectors_almost_equal
import physics

from world import World

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
    connections = s.extract_connections_map()
    for block_index, block_connections in connections.items():
        for edge_index, connected in block_connections.items():
            a, b = connected
            assert connections[ a ][ b ] == (block_index, edge_index)
    assert len( s.extract_connections() ) == 4

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
    connections = s.extract_connections_map()
    for block_index, block_connections in connections.items():
        for edge_index, connected in block_connections.items():
            a, b = connected
            assert connections[ a ][ b ] == (block_index, edge_index)
    assert len( s.extract_connections() ) == 3

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
    connections = s.extract_connections_map()
    for block_index, block_connections in connections.items():
        for edge_index, connected in block_connections.items():
            a, b = connected
            assert connections[ a ][ b ] == (block_index, edge_index)
    assert len( s.extract_connections() ) == 3

def test_integer_map_setitem_regression():
    x = IntegerMap()
    assert x.next_index == 0
    x[ x.next_index ] = 10
    assert x.next_index == 1
    assert list(x.indexed()) == [ (0,10) ]
    y = IntegerMap()
    assert y.next_index == 0
    y.append( 10 )
    assert y.next_index == 1
    assert list(y.indexed()) == [ (0,10) ]

def test_integer_map():
    x = IntegerMap()
    for i in range(10):
        assert x.next_index == i
        x.append( "foo {0}".format( i ) )
    for i in range(10):
        assert x[i] == "foo {0}".format( i )
    assert [ "foo {0}".format(i) for i in range(10) ] == [ s for s in x ]
    del x[7]
    for i in range(10):
        if i != 7:
            assert x[i] == "foo {0}".format( i )
    assert x.next_index == 10
    x.append( "last" )
    assert x[ x.next_index - 1 ] == "last"

def test_reshape():
    w = World()
    w.sim = physics.PhysicsSimulator( timestep = None )
    a = QuadBlock(32)
    b = QuadBlock(35)
    thing = physics.Thing( w, BlockStructure(a).create_collision_shape(), 1.0, 1.0 )
    w.sim.perform_removals_and_additions()
    assert thing.abstract_shape.area() == a.area()
    thing.reshape( BlockStructure(b).create_collision_shape() )
    assert thing.abstract_shape.area() == b.area()
    w.sim.perform_removals_and_additions()

def test_reshape_twice():
    w = World()
    w.sim = physics.PhysicsSimulator( timestep = None )
    a = QuadBlock(32)
    b = QuadBlock(35)
    thing = physics.Thing( w, BlockStructure(a).create_collision_shape(), 1.0, 1.0 )
    w.sim.perform_removals_and_additions()
    assert thing.abstract_shape.area() == a.area()
    thing.reshape( BlockStructure(b).create_collision_shape() )
    assert thing.abstract_shape.area() == b.area()
    thing.reshape( BlockStructure(a).create_collision_shape() )
    assert thing.abstract_shape.area() == a.area()
    w.sim.perform_removals_and_additions()

def test_reshape_early():
    w = World()
    w.sim = physics.PhysicsSimulator( timestep = None )
    a = QuadBlock(32)
    b = QuadBlock(35)
    thing = physics.Thing( w, BlockStructure(a).create_collision_shape(), 1.0, 1.0 )
    assert thing.abstract_shape.area() == a.area()
    thing.reshape( BlockStructure(b).create_collision_shape() )
    assert thing.abstract_shape.area() == b.area()
    w.sim.perform_removals_and_additions()

def test_regression_bigger_block_structure():
    #  2
    # 3 1
    #  0

    # 147
    # 0369
    # 258
    s = BlockStructure( QuadBlock(32) )
    assert (0,2) in s.free_edge_indices
    s.attach((0,2), QuadBlock(32), 0)
    assert (0,2) not in s.free_edge_indices

    assert len( s.blocks ) == 2
    for blockno, n in zip( range(10), (3,3) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n

    assert (0,0) in s.free_edge_indices
    s.attach((0,0), QuadBlock(32), 2)
    assert (0,0) not in s.free_edge_indices
    assert (0,1) in s.free_edge_indices
    s.attach((0,1), QuadBlock(32), 3)
    assert (0,1) not in s.free_edge_indices

    assert len( s.blocks ) == 4
    for blockno, n in zip( range(10), (1,3,3,3) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n

    assert (3,2) in s.free_edge_indices
    s.attach((3,2), QuadBlock(32), 0)
    assert (3,2) not in s.free_edge_indices
    assert (3,0) in s.free_edge_indices
    s.attach((3,0), QuadBlock(32), 2)
    assert (3,0) not in s.free_edge_indices
    assert (3,1) in s.free_edge_indices
    s.attach((3,1), QuadBlock(32), 3)
    assert (3,1) not in s.free_edge_indices

    assert len( s.blocks ) == 7
    for blockno, n in zip( range(10), (1,2,2,0,2,2,3) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n

    assert (6,2) in s.free_edge_indices
    s.attach((6,2), QuadBlock(32), 0)
    assert (6,2) not in s.free_edge_indices

    assert len( s.blocks ) == 8
    for blockno, n in zip( range(10), (1,2,2,0,1,2,2,2) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n

    assert (6,0) in s.free_edge_indices

    s.attach((6,0), QuadBlock(32), 2)

    assert (6,0) not in s.free_edge_indices

    assert len( s.blocks ) == 9
    for blockno, n in zip( range(10), (1,2,2,0,1,1,1,2,2) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n

    assert (6,1) in s.free_edge_indices
    s.attach((6,1), QuadBlock(32), 3)
    assert len( s.blocks ) == 10
    for blockno, n in zip( range(10), (1,2,2,0,1,1,0,2,2,3) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n
    assert len( s.free_edge_indices ) == 14

def test_regression_bigger_block_structure2():
    #  2
    # 3 1
    #  0

    # 147
    # 0369
    # 258
    s = BlockStructure( QuadBlock(32) )
    assert (0,2) in s.free_edge_indices
    s.attach((0,2), QuadBlock(32), 0)
    assert (0,2) not in s.free_edge_indices

    assert len( s.blocks ) == 2
    for blockno, n in zip( range(10), (3,3) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n
        assert len(s.blocks[blockno].free_edge_indices) == n

    assert (0,0) in s.free_edge_indices
    s.attach((0,0), QuadBlock(32), 2)
    assert (0,0) not in s.free_edge_indices
    assert (0,1) in s.free_edge_indices
    s.attach((0,1), QuadBlock(32), 3)
    assert (0,1) not in s.free_edge_indices

    assert len( s.blocks ) == 4
    for blockno, n in zip( range(10), (1,3,3,3) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n
        assert len(s.blocks[blockno].free_edge_indices) == n

    assert (3,2) in s.free_edge_indices
    s.attach((3,2), QuadBlock(32), 0)
    assert (3,2) not in s.free_edge_indices
    assert (3,0) in s.free_edge_indices
    s.attach((3,0), QuadBlock(32), 2)
    assert (3,0) not in s.free_edge_indices
    assert (3,1) in s.free_edge_indices
    s.attach((3,1), QuadBlock(32), 3)
    assert (3,1) not in s.free_edge_indices

    assert len( s.blocks ) == 7
    for blockno, n in zip( range(10), (1,2,2,0,2,2,3) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n
        assert len(s.blocks[blockno].free_edge_indices) == n

    assert (6,2) in s.free_edge_indices
    s.attach((6,2), QuadBlock(32), 0)
    assert (6,2) not in s.free_edge_indices

    assert len( s.blocks ) == 8
    for blockno, n in zip( range(10), (1,2,2,0,1,2,2,2) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n
        assert len(s.blocks[blockno].free_edge_indices) == n

    assert (6,0) in s.free_edge_indices

    s.attach((6,0), QuadBlock(32), 2)

    assert (6,0) not in s.free_edge_indices

    assert len( s.blocks ) == 9
    for blockno, n in zip( range(10), (1,2,2,0,1,1,1,2,2) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n
        assert len(s.blocks[blockno].free_edge_indices) == n

    assert (6,1) in s.free_edge_indices
    s.attach((6,1), QuadBlock(32), 3)
    assert len( s.blocks ) == 10
    for blockno, n in zip( range(10), (1,2,2,0,1,1,0,2,2,3) ):
        assert len( filter( lambda (a,_): a == blockno, s.free_edge_indices ) ) == n
        assert len(s.blocks[blockno].free_edge_indices) == n
    assert len( s.free_edge_indices ) == 14
