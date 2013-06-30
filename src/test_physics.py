import random
import math
import pytest

from test_util import almost_equal, almost_leq, almost_geq

from test_util import radians_to_degrees, degrees_to_radians

from physics import *

def test_physics_limit_calculations():
    for i in range(100):
        diameter = random.random()
        speed = random.random()
        timestep = random.random()
        assert almost_equal( calculate_maximum_timestep( diameter, speed ) * speed, 0.5 * diameter )
        assert almost_equal( timestep * calculate_maximum_speed( timestep, diameter ), 0.5 * diameter )
        assert almost_equal( timestep * speed, 0.5 * calculate_minimum_diameter( timestep, speed ) )

def test_closed_circle():
    assert list(closed_circle([1,2,3])) == [1,2,3,1]
    assert list(closed_circle([1])) == [1,1]
    assert list(closed_circle(xrange(10))) == range(10) + [0]
    assert list(closed_circle([])) == []

def test_successive_pairs():
    assert list(successive_pairs([1,2,3,4,5])) == [(1,2),(2,3),(3,4),(4,5)]
    assert list(successive_pairs([1])) == []
    assert list(successive_pairs([])) == []

def test_closed_circle_pairs():
    assert list(closed_circle_pairs([1,2,3,4,5])) == [(1,2),(2,3),(3,4),(4,5),(5,1)]
    assert list(closed_circle_pairs([1])) == [(1,1)]
    assert list(closed_circle_pairs([])) == []

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

def test_polygon_area():
    for j in range(100):
        r = random.random() * 10.0
        x0, y0 = (random.random() - 0.5) * 10.0, (random.random() - 0.5) * 10.0
        circle_points = [(x0 + r * math.cos(0.001*i), y0 + r * math.sin(0.001*i)) for i in range(6283)]
        assert almost_equal( math.pi * r * r, ConvexPolygonShape(*circle_points).area() )
    for j in range(100):
        w, h = random.random() * 10.0, random.random() * 10.0
        x0, y0 = (random.random() - 0.5) * 10.0, (random.random() - 0.5) * 10.0
        box_points = [ (x0,y0), (x0+w,y0), (x0+w,y0+h), (x0,y0+h) ]
        assert almost_equal( w * h, ConvexPolygonShape(*box_points).area() )

def test_disk_area():
    for j in range(100):
        r = random.random() * 10.0
        x0, y0 = (random.random() - 0.5) * 10.0, (random.random() - 0.5) * 10.0
        assert almost_equal( math.pi * r * r, DiskShape(r, (x0,y0)).area() ) 

def test_polygon_centroid():
    for j in range(100):
        r = random.random() * 10.0
        x0, y0 = (random.random() - 0.5) * 10.0, (random.random() - 0.5) * 10.0
        circle_points = [(x0 + r * math.cos(0.001*i), y0 + r * math.sin(0.001*i)) for i in range(6283)]
        centroid = ConvexPolygonShape(*circle_points).centroid()
        print >> sys.stderr, r, (x0,y0), centroid
        assert almost_equal( x0, centroid.x )
        assert almost_equal( y0, centroid.y )
    for j in range(100):
        w, h = random.random() * 10.0, random.random() * 10.0
        x0, y0 = (random.random() - 0.5) * 10.0, (random.random() - 0.5) * 10.0
        box_points = [ (x0,y0), (x0+w,y0), (x0+w,y0+h), (x0,y0+h) ]
        centroid = ConvexPolygonShape(*box_points).centroid()
        assert almost_equal( x0 + 0.5 * w, centroid.x )
        assert almost_equal( y0 + 0.5 * h, centroid.y )

def test_disk_centroid():
    for j in range(100):
        r = random.random() * 10.0
        x0, y0 = (random.random() - 0.5) * 10.0, (random.random() - 0.5) * 10.0
        cx, cy = DiskShape(r, (x0,y0)).centroid()
        assert almost_equal( x0, cx )
        assert almost_equal( y0, cy )

def test_composite_area():
    for j in range(100):
        w, h = (random.random()+1.0) * 10.0, random.random() * 10.0
        x0, y0 = (random.random() - 0.5) * 10.0, (random.random() - 0.5) * 10.0
        box_points = [ (x0,y0), (x0+w,y0), (x0+w,y0+h), (x0,y0+h) ]
        negative_box_points = [ (-x0,y0), (-x0+w,y0), (-x0+w,y0+h), (-x0,y0+h) ]
        area = CompositeShape(ConvexPolygonShape(*box_points), ConvexPolygonShape(*negative_box_points)).area()
        assert almost_equal( 2.0 * (w*h), area )

def test_composite_centroid():
    for j in range(100):
        w, h = (random.random()) * 10.0, random.random() * 10.0
        x0, y0 = (random.random() + 1) * 10.0, (random.random() - 0.5) * 10.0
        box_points = [ (x0,y0), (x0+w,y0), (x0+w,y0+h), (x0,y0+h) ]
        negative_box_points = [ (-x0,y0), (-x0-w,y0), (-x0-w,y0+h), (-x0,y0+h) ]
        centroid = CompositeShape(ConvexPolygonShape(*box_points), ConvexPolygonShape(*negative_box_points)).centroid()
        centroid_1 = ConvexPolygonShape(*box_points).centroid()
        centroid_2 = ConvexPolygonShape(*negative_box_points).centroid()
        assert almost_equal( centroid.x, (centroid_1.x+centroid_2.x) * 0.5 )
        assert almost_equal( centroid.y, (centroid_1.y+centroid_2.y) * 0.5 )

def test_group_id_generation():
    sim = PhysicsSimulator()
    group_ids = [ sim.new_group_id() for i in xrange(100000) ]
    assert len(group_ids) == len(set(group_ids))
    assert all( [ x > 0 for x in group_ids ] )

def test_timestep_fixed():
    timestep = 0.01
    sim = PhysicsSimulator(timestep = timestep, size_limit = 10.0, speed_limit = None)
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
