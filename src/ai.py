from util import *

def ai_flee_target( dt, actor, target):
    actor._ai_time += dt
    if actor._ai_time > 0.01:
        actor._ai_time = 0.0
        delta = (target.position - actor.position)
        distance = delta.get_length()
        correctness = delta.normalized().dot( -actor.direction )
        angle = radians_to_degrees( math.acos( correctness ) )
        sangle = (radians_to_degrees( math.atan2( delta.y, delta.x ) ) - actor.angle_degrees) % 360.0 - 180.0
        actor._turbo = False
        if distance < 500.0:
            forwards = angle < 90.0
        else:
            forwards = angle < 20.0
        last_spin = actor._spin
        new_spin = -sign(sangle)
        actor._spin = 0 if abs(sangle) < 15.0 else new_spin
        if forwards:
            actor._thrusting = True
            actor._braking = False
        else:
            actor._thrusting = False
            actor._braking = True

def ai_seek_target( dt, actor, target, fire):
    actor._ai_time += dt
    if actor._ai_time > 0.01:
        actor._ai_time = 0.0
        delta = (target.position - actor.position)
        distance = delta.get_length()
        correctness = delta.normalized().dot( actor.direction )
        angle = radians_to_degrees( math.acos( correctness ) )
        sangle = (radians_to_degrees( math.atan2( delta.y, delta.x ) ) - actor.angle_degrees + 180.0) % 360.0 - 180.0
        print "actor-angle", actor.angle_degrees % 360.0
#        print "delta", delta
#        print "sangle", sangle
        actor._turbo = False
        if distance > 500.0:
            forwards = angle < 90.0
        else:
            forwards = angle < 20.0
        last_spin = actor._spin
        new_spin = -sign(sangle)
        may_fire = target.alive and actor.may_fire() and distance < 1000.0
        if may_fire:
            # note that by using _relative_ velocity here we actually lead our target
            # we need to assume a bullet velocity
            shot_angle = (actor.direction * 1400 + actor.velocity - target.velocity).get_angle_degrees()
            aim_angle = (radians_to_degrees( math.atan2( delta.y, delta.x ) ) - shot_angle + 180.0) % 360.0 - 180.0
            actor._spin = -sign(aim_angle)
        elif new_spin != last_spin:
            actor._spin = 0 if abs(sangle) < 15.0 else new_spin
        if forwards:
            actor._thrusting = True
            actor._braking = False
        else:
            actor._thrusting = False
            actor._braking = True
        if may_fire:
            if aim_angle < 5.0:
                fire()
