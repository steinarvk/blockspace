from physics import ConvexPolygonShape, DiskShape, Vec2d
from ship import Debris

import physics

from util import *

def create_pellet(world, shooter, gun):
    points = [(0,0),(9,0),(9,33),(0,33)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
#    shape = DiskShape(5) # useful for debugging with pygame to see bullet origins
    layer = None
    rv = Debris( world, layer, (0,0), shape, None, mass = 1.0, moment = physics.infinity, collision_type = physics.CollisionTypes["bullet"], group = physics.CollisionGroups["bullets"] )
    speed = 1400
#    speed = 0
    base_velocity = gun.velocity
    base_velocity = shooter.velocity # unrealistic but possibly better
    rv.velocity = base_velocity + gun.direction * speed
    rv.position = gun.position
    rv.angle_radians = degrees_to_radians( gun.angle_degrees + 90.0 ) # realistic
#    rv.angle_radians = degrees_to_radians( rv.velocity.get_angle_degrees() + 999.0 ) # might look better
    rv.inert = False
    rv.grace = 0.15
    rv.shooter = shooter
    kw = {}
    kw[ "size" ] = 9.0,33.0
    kw[ "texture_size" ] = world.atlas.texsize( "laserGreen" )
    kw[ "texture_coordinates" ] = world.atlas.texcoords( "laserGreen" )
    kw[ "position" ] = rv.position
    kw[ "angle" ] = rv.angle_radians
    kw[ "colour" ] = (0.0,1.0,0.0,1.0)
    rv.index = world.object_psys.add( **kw )
    world.psys_managed_things.append( (rv, rv.index) )
    def update_bullet( bullet, dt ):
        if not bullet.alive:
            return
        bullet.ttl -= dt
        bullet.grace -= dt
        if bullet.ttl <= 0.0:
            bullet.kill()
    def kill_bullet( rv ):
        world.psys_managed_things.remove( (rv,rv.index) )
        world.object_psys.remove( rv.index )
    rv.ttl = 1.5
    rv.kill_hooks.append( kill_bullet )
    world.pre_physics.add_hook( rv, partial(update_bullet,rv) )

def create_dumb_missile(world, shooter, gun):
    points = [(0,0),(9,0),(9,33),(0,33)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
    layer = None
    rv = Debris( world, layer, (0,0), shape, None, mass = 1.0, moment = physics.infinity, collision_type = physics.CollisionTypes["bullet"], group = physics.CollisionGroups["bullets"] )
    speed = 10
    acceleration = Vec2d(gun.direction) * 1500
    base_velocity = gun.velocity
    base_velocity = shooter.velocity # unrealistic but possibly better
    rv.velocity = base_velocity + gun.direction * speed
    rv.position = gun.position
    rv.angle_radians = degrees_to_radians( gun.angle_degrees + 90.0 ) # realistic
    rv.inert = False
    rv.grace = 0.5
    rv.shooter = shooter
    rv.lifetime = 0.0
    kw = {}
    kw[ "size" ] = 9.0,33.0
    kw[ "texture_size" ] = world.atlas.texsize( "laserGreen" )
    kw[ "texture_coordinates" ] = world.atlas.texcoords( "laserGreen" )
    kw[ "position" ] = rv.position
    kw[ "angle" ] = rv.angle_radians
    kw[ "colour" ] = (0.4,0.4,1.0,1.0)
    rv.index = world.object_psys.add( **kw )
    world.psys_managed_things.append( (rv, rv.index) )
    def update_bullet( bullet, dt ):
        if not bullet.alive:
            return
        bullet.lifetime += dt
        bullet.grace -= dt
        if bullet.lifetime > 0.2:
            bullet.velocity += acceleration * dt
        if bullet.ttl <= bullet.lifetime:
            bullet.kill()
    def kill_bullet( rv ):
        world.psys_managed_things.remove( (rv,rv.index) )
        world.object_psys.remove( rv.index )
    rv.ttl = 1.5
    rv.kill_hooks.append( kill_bullet )
    world.pre_physics.add_hook( rv, partial(update_bullet,rv) )
