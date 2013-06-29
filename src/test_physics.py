from physics import *

def test_shape_creation():
    body = pymunk.Body()
    [sh,] = TriangleShape( (0,0), (1,0), (0,1), sensor = True ).generate_shapes( body )
    assert sh.sensor
    [sh,] = TriangleShape( (0,0), (1,0), (0,1), sensor = False ).generate_shapes( body )
    assert not sh.sensor
    [sh,] = SegmentShape( (0,0), (1,0), group = 43 ).generate_shapes( body )
    assert sh.group == 43
    [sh,] = SegmentShape( (0,0), (1,0), group = 44 ).generate_shapes( body )
    assert sh.group == 44
    [sh,] = ConvexPolygonShape( (0,0), (1,0), (0,1), collision_type = 2 ).generate_shapes( body )
    assert sh.collision_type == 2
    [sh,] = ConvexPolygonShape( (0,0), (1,0), (0,1), collision_type = 3 ).generate_shapes( body )
    assert sh.collision_type == 3
    [sh1, sh2] = CompositeShape( TriangleShape( (0,0), (1,0), (0,1), collision_type = 3, group = 4, sensor = True ),
                                 TriangleShape( (1,0), (2,0), (1,1), collision_type = 8, group = 9, sensor = False ),
                                 sensor = False,
                                 group = 12 ).generate_shapes( body )
    assert sh1.collision_type == 3
    assert sh2.collision_type == 8
    assert not sh1.sensor
    assert not sh2.sensor
    assert sh1.group == 12
    assert sh2.group == 12

