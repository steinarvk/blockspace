from component import *
from blocks import *
from world import World
from physics import Thing, Vec2d, PhysicsSimulator
from math import pi
import random

from util import *

def rnd():
    import random
    return 360 * 2 * (random.random() - 0.5)

def rnd2():
    return rnd(), rnd()

def setup_world():
    w = World()
    w.sim = PhysicsSimulator( timestep = None )
    block = QuadBlock(32)
    bs = BlockStructure(block)
    thing = Thing( w, bs.create_collision_shape(), 1.0, 1.0 )
    return block, thing

def test_point_component_at_origin():
    block, thing = setup_world()
    component = PointComponent( block, (0,0), 0.0 )
    assert component.position == block.position
    assert component.position == Vec2d(0,0)
    assert component.angle_degrees == block.angle_degrees
    assert component.angle_degrees == 0.0

def create_and_check_point_component( thing_xy, thing_angle, vel, angvel, comp_xy, comp_angle ):
    comp_xy = Vec2d(comp_xy)
    thing_xy = Vec2d(thing_xy)
    vel = Vec2d(vel)
    block, thing = setup_world()
    thing.position = thing_xy
    thing.angle_degrees = thing_angle
    thing.velocity = vel
    thing.angular_velocity_degrees = angvel
    component = PointComponent( block, comp_xy, comp_angle )
    assert almost_equal( component.position.get_distance( thing.position ), comp_xy.get_length() )
    assert degrees_almost_equal( component.angle_degrees, thing.angle_degrees + comp_angle )
    return component, block, thing

def test_point_components_basic_zero():
    create_and_check_point_component( (0,0), 0.0, (0,0), 0.0, (0,0), 0.0 )

def test_point_components_random_basic():
    for i in range(1000):
        create_and_check_point_component( rnd2(), rnd(), rnd2(), rnd(), rnd2(), rnd() )

def test_point_components_random_pure_rotational_velocity_at_zero_angle():
    for i in range(1000):
        a = rnd()
        r = rnd()
        c, _, _ = create_and_check_point_component( rnd2(), 0.0, (0,0), a, Vec2d(r,0), rnd() )
        assert vectors_almost_equal( c.velocity, (0, pi * r * a / 180.0) )

def test_point_components_random_pure_rotational_velocity():
    for i in range(1000):
        a = rnd()
        r = rnd()
        ang = rnd()
        c, _, _ = create_and_check_point_component( rnd2(), ang, (0,0), a, Vec2d(r,0), rnd() )
        assert vectors_almost_equal( c.velocity, Vec2d(0, pi * r * a / 180.0).rotated_degrees(ang) )

def test_point_components_random_pure_linear_velocity():
    for i in range(1000):
        a = rnd()
        v = rnd2()
        c, _, thing = create_and_check_point_component( rnd2(), rnd(), v, 0.0, rnd2(), rnd() )
        assert vectors_almost_equal( c.velocity, v )
        assert vectors_almost_equal( c.velocity, thing.velocity )

def test_point_components_random_combined_velocities():
    for i in range(1000):
        a = rnd()
        r = rnd()
        ang = rnd()
        v = rnd2()
        c, block, thing = create_and_check_point_component( rnd2(), ang, v, a, Vec2d(r,0), rnd() )
        print thing.velocity, v, c.velocity
        assert vectors_almost_equal( c.velocity - thing.velocity, Vec2d(0, pi * r * a / 180.0).rotated_degrees(ang) )

def test_basic_power_supply():
    psu = PowerSupply( 1000 )
    assert psu.power == 0
    psu.set_production( "generator", 3 )
    for i in range(167):
        assert psu.power == min(1000,(6*i))
        psu.tick(2)
    for i in range(500):
        assert psu.power == 1000
        psu.tick(2)
    psu.set_consumption( "thruster", 53.0 )
    for i in range(10):
        assert psu.power == (1000 - 100 * i)
        psu.tick(2)

def test_power_supply_production_override():
    psu = PowerSupply( 1000 )
    assert psu.power == 0
    psu.set_production( "generator", 2 )
    psu.set_production( "generator", 3 )
    for i in range(167):
        assert psu.power == min(1000,(6*i))
        psu.tick(2)

def test_power_supply_production_combine():
    psu = PowerSupply( 1000 )
    assert psu.power == 0
    psu.set_production( "generator1", 1 )
    psu.set_production( "generator2", 2 )
    for i in range(167):
        assert psu.power == min(1000,(6*i))
        psu.tick(2)

def test_power_supply_consumption_override():
    psu = PowerSupply( 1000 )
    psu.power = 1000
    psu.set_consumption( "thruster", 1 )
    psu.set_consumption( "thruster", 3 )
    for i in range(100):
        assert psu.power == 1000 - 6 * i
        psu.tick(2)

def test_power_supply_consumption_combine():
    psu = PowerSupply( 1000 )
    psu.power = 1000
    psu.set_consumption( "thruster1", 2 )
    psu.set_consumption( "thruster2", 3 )
    for i in range(100):
        assert psu.power == 1000 - 10 * i
        psu.tick(2)

def test_create_battery_component():
    import serialization
    block = create_block(4)
    ctx = { "block" : block }
    battery1 = create_component( "battery", ctx, storage = 300 )
    battery2 = create_component( "battery", ctx, storage = 500 )
    for battery in (battery1, battery2):
        assert battery.block == block
        assert battery in block.components
    assert battery1.storage == 300
    assert battery2.storage == 500
    battery1_serialized = serialization.serialize_original( battery1 )
    battery2_serialized = serialization.serialize_original( battery2 )
    battery1_ = serialization.unserialize_original( ctx, battery1_serialized )
    battery2_ = serialization.unserialize_original( ctx, battery2_serialized )
    assert battery1.storage == battery1_.storage
    assert battery2.storage == battery2_.storage
