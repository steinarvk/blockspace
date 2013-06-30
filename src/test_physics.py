import random
import math
import pytest

from test_util import almost_equal, almost_leq, almost_geq

from test_util import radians_to_degrees, degrees_to_radians

from physics import *

def test_shape_creation():
    body = pymunk.Body()
    [sh,] = DiskShape( 1.0, elasticity = 0.5 ).generate_shapes( body )
    assert sh.elasticity == 0.5
    [sh,] = DiskShape( 1.0, elasticity = 0.6 ).generate_shapes( body )
    assert sh.elasticity == 0.6
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

def test_group_id_generation():
    sim = PhysicsSimulator()
    group_ids = [ sim.new_group_id() for i in xrange(100000) ]
    assert len(group_ids) == len(set(group_ids))
    assert all( [ x > 0 for x in group_ids ] )

def test_timestep_fixed():
    timestep = 0.01
    sim = PhysicsSimulator(timestep = timestep)
    timesteps = []
    def fake_timestep(dt):
        timesteps.append( dt )
    sim.space.step = fake_timestep
    t = 0.0
    for i in range(1000):
        dt = random.random()
        t += dt
        sim.tick( dt )
    assert len(set(timesteps)) == 1
    assert len(timesteps) == int(t / timestep)

def test_create_thing():
    sim = PhysicsSimulator()
    thing = Thing( sim, DiskShape(10.0), mass = 1.0, moment = 1.0 ) 
    assert thing.name == "anonymous"
    assert thing.position == (0,0)
    assert thing.velocity == (0,0)
    assert thing.body in sim.space.bodies

def test_thing_vector_getter():
    sim = PhysicsSimulator()
    thing = Thing( sim, DiskShape(10.0), mass = 1.0, moment = 1.0 ) 
    pos = thing.position
    vel = thing.velocity
    assert thing.position == (0,0)
    assert thing.velocity == (0,0)
    pos += (1,0)
    vel += (2,1)
    assert thing.position == (0,0)
    assert thing.velocity == (0,0)

def test_constant_velocity():
    sim = PhysicsSimulator()
    thing = Thing( sim, DiskShape(10.0), mass = 1.0, moment = 1.0 ) 
    original_position = thing.position
    v = 100.0
    t = 60.0
    thing.velocity = (v,0)
    sim.tick( t )
    final_position = thing.position
    assert original_position.get_distance( final_position ) > (0.5 * v * t)
    assert almost_leq( original_position.get_distance( final_position ), (v * t) )

def test_collision_with_wall():
    sim = PhysicsSimulator()
    thing = Thing( sim, DiskShape(10.0), mass = 1.0, moment = 1.0 ) 
    wall_x = 100
    obstacle = StaticObstacle( sim, SegmentShape((wall_x,-100),(wall_x,100)) )
    v = 100.0
    t = 60.0
    thing.velocity = (v,0)
    sim.tick( t )
    assert thing.position.x < wall_x

def test_bounce_with_wall():
    sim = PhysicsSimulator()
    thing = Thing( sim, DiskShape(10.0, elasticity = 0.9), mass = 1.0, moment = 1.0 ) 
    wall_x = 100
    obstacle = StaticObstacle( sim, SegmentShape((wall_x,-100),(wall_x,100), elasticity = 0.9) )
    v = 100.0
    t = 60.0
    thing.velocity = (v,0)
    sim.tick( t )
    assert thing.position.x < -100.0

def test_thing_angles():
    sim = PhysicsSimulator()
    thing = Thing( sim, DiskShape(10.0), mass = 1.0, moment = 1.0 ) 
    thing.angular_velocity_radians = 1.0
    angles = []
    for i in range(6000):
        sim.tick(0.01)
        radians = thing.angle_radians
        degrees = thing.angle_degrees
        angles.append( radians )
        assert almost_equal( math.cos( radians ), math.cos( degrees_to_radians( degrees ) ) )
        assert almost_equal( math.sin( radians ), math.sin( degrees_to_radians( degrees ) ) )
    assert len( set(angles) ) > 1

def test_max_speed_collision_with_wall():
    for i in range(100):
        sim = PhysicsSimulator()
        thing = Thing( sim, DiskShape(0.5*sim.object_size_lower_limit), mass = 1.0, moment = 1.0 ) 
        wall_x = 100
        obstacle = StaticObstacle( sim, SegmentShape((wall_x,-100),(wall_x,100)) )
        thing.position = (random.random(), 0)
        v = sim.speed_limit
        t = 30.0
        thing.velocity = (v,0)
        sim.tick( t )
        assert thing.position.x < wall_x

def test_raise_on_too_small_thing():
    with pytest.raises( AssertionError ):
        sim = PhysicsSimulator()
        thing = Thing( sim, DiskShape(0.4 * sim.object_size_lower_limit), mass = 1.0, moment = 1.0 ) 
        
if __name__ == '__main__':
    test_raise_on_too_small_thing()
