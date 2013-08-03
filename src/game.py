import graphics
import physics
import gameinput
import ai

from atlas import Atlas

from physics import ConvexPolygonShape, DiskShape, Vec2d
from gameinput import key

import cocos

import random

from util import *

from pyglet.gl import *

from bsc import include_build_directory
include_build_directory()

import bsgl
from functools import partial
from itertools import cycle

import pygame
from pymunk.pygame_util import draw_space
import pymunk

import blocks
import component
from component import create_component

from operator import attrgetter

from world import World

from ship import Ship, Debris, create_ship_thing

def create_square_thing(world, layer, position, image):
    points = [(0,0),(32,0),(32,32),(0,32)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
    moment = pymunk.moment_for_poly( 1.0, shape.vertices )
    rv = Debris( world, layer, position, shape, image, moment = moment, collision_type = physics.CollisionTypes["main"] )
    return rv

class MainWorld (World):
    def __init__(self, window, player_ship_data = None, use_pygame = False, **kwargs):
        super( MainWorld, self ).__init__( **kwargs)
        self.window = window
        resolution = (self.window.width, self.window.height )
        self.setup_graphics( resolution )
        self.setup_game( player_ship_data = player_ship_data )
        self.setup_input()
        self.setup_hud()
        self.camera.following = self.player
        self.main_layer.camera = self.camera
        if use_pygame:
            self.setup_pygame( resolution )
            self.display.add_anonymous_hook( self.update_pygame )
        self.pre_display.add_anonymous_hook( self.update_psys_managed_objects )
        self.pre_physics.add_anonymous_hook( self.update_camera )
        self.display.add_anonymous_hook( self.scene.update )
        self.player.body.velocity_limit = 800.0 # experiment with this for actually chasing fleeing ships
        self.pre_physics.add_hook( self.player, self.player.update )
        self.pre_physics.add_hook( self.enemy, lambda dt : ai.ai_seek_target( dt, self.enemy, self.player, partial( self.shoot_volley, self.enemy ) ) )
#        self.pre_physics.add_hook( self.enemy, lambda dt : ai.ai_flee_target( dt, self.enemy, self.player ) )
        self.pre_physics.add_hook( self.enemy, self.enemy.update )
        self.pre_physics.add_hook( self.enemy2, lambda dt : ai.ai_seek_target( dt, self.enemy2, self.player, partial( self.shoot_volley, self.enemy2 ) ) )
#        self.pre_physics.add_hook( self.enemy2, lambda dt : ai.ai_flee_target( dt, self.enemy2, self.player ) )
        self.pre_physics.add_hook( self.enemy2, self.enemy2.update )
        for x in (self.player, self.enemy, self.enemy2):
            self.post_physics.add_hook( x, x.tick )
            x.add_to_minimap( self.minimap, "solid_white_5x5.png", (0,255,0) if x == self.player else (255,0,0) )
#        for x in self.things:
#            x.add_to_minimap( self.minimap, "solid_white_5x5.png", (128,128,128) )
        self.physics.add_anonymous_hook( self.sim.tick )
        self.scene.schedule( self.update_everything )
    def on_save_ship(self, *args):
        import sys
        s = self.player.dump_string()
        print >> sys.stderr, s
        self.player.dump_file( "dumped_ship.yaml" )
    def update_everything(self, dt):
        self.tick( dt )
        self.display_update()
    def update_camera(self, dt):
        self.camera.update( dt )
    def setup_pygame(self, resolution):
        pygame.init()
        self.screen = pygame.display.set_mode( resolution )
    def setup_graphics(self, resolution):
        self.camera = graphics.Camera( self.window )
        self.scene = graphics.Scene( self.window )
        graphics.Layer( self.scene, cocos.layer.ColorLayer( 0, 0, 0, 1 ) )
        for i in range(8):
            graphics.Layer( self.scene, graphics.BackgroundCocosLayer( self.camera, 10.0 + 0.5 * i, "starfield{0}.png".format(i) ) )
        self.hud_width = 170
        self.main_layer = graphics.Layer( self.scene )
        self.main_layer.cocos_layer.position = self.camera.offset()
        self.main_layer.size = (self.window.width-self.hud_width,self.window.height)
        self.hud_cocos_layer = graphics.BlankingCocosLayer()
        self.hud_cocos_layer.clear_colour = (0,40,40,255)
        self.hud_cocos_layer.clear_rect = ((self.window.width-self.hud_width,0),(self.window.width,0),(self.window.width,self.window.height),(self.window.width-self.hud_width,self.window.height))
        self.hud_layer = graphics.Layer( self.scene, cocos_layer = self.hud_cocos_layer )
        self.hud_layer.cocos_layer.position = 0,0
        self.gem_images = pyglet.image.ImageGrid( pyglet.image.load("gems3.png"), 4, 4 )
        self.atlas = Atlas( "atlas.generated" )
        self.object_psys = bsgl.System( texture_id = self.atlas.sheet.get_texture().id )
        self.hud_psys = bsgl.System( texture_id = self.atlas.sheet.get_texture().id )
    def setup_hud(self):
        def update_hp_display():
            undamaged = 255,255,255
            undamaged_cockpit = 0,255,0
            damaged = damaged_cockpit = 255,0,0
#            for block, sprite in self.hud_sprite.subcomponent.items():
#                rel = float(block.hp) / block.max_hp
#                a = damaged_cockpit if block.cockpit else damaged
#                b = undamaged_cockpit if block.cockpit else undamaged
#                sprite.color = vector_lerp( rel, a, b )
#                cockpit = False
        def create_hp_display():
            self.hud_sprite = self.player.block_structure.create_sys_structure( self.hud_psys, self.atlas, self.player, sync_to_thing = False )
            expected_size = self.hud_width
            update_hp_display()
        def recreate_hp_display():
            self.hud_sprite.kill()
            create_hp_display()
        
        bar = graphics.VerticalBar( 8, 256, (0,64,0), (128,0,0) )
        bar.position = (self.window.width - self.hud_width + 16), (self.window.height - self.hud_width - bar.height)
        x, y = self.window.width - self.hud_width + 32, self.window.height - self.hud_width
        speed_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        power_supply_size_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        power_production_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        thrust_power_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        turn_power_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        brake_power_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        number_of_engines_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        number_of_guns_label = last_element = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        y -= last_element.height + 8
        x, y = self.window.width - self.hud_width + 16, self.window.height - self.hud_width - bar.height - 16
        position_label = graphics.create_label( x, y, layer = self.hud_cocos_layer )
        def update_labels():
            x, y = self.player.position
            position_label.element.text = "({0},{1})".format( int(x*0.1), int(y*0.1) )
            speed_label.element.text = "S: {0:.1f}".format( self.player.speed )
            power_production_label.element.text = "PP: {0}".format( int(sum( self.player.psu.production.values() ) ) )
            power_supply_size_label.element.text = "MP: {0}".format( int(self.player.psu.max_storage) )
            thrust_power_label.element.text = "T: {0}".format( self.player.thrust_power )
            turn_power_label.element.text = "R: {0}".format( self.player.turn_power )
            brake_power_label.element.text = "B: {0}".format( self.player.brake_power )
            number_of_engines_label.element.text = "#E: {}".format( len( self.player.all_engines() ) )
            number_of_guns_label.element.text = "#G: {0}/{1}".format( len( self.player.ready_guns() ), len( self.player.all_guns() ) )
        def update_power_display():
            bar.fill = self.player.psu.charge_rate()
        self.hud_cocos_layer.add( bar )
        self.minimap = graphics.Minimap( self.hud_width - 32, self.hud_width - 32, 5000, 5000, self.player )
        self.minimap.position = (self.window.width - self.hud_width + 16), (self.window.height - self.hud_width - bar.height - self.hud_width - 16)
        self.hud_cocos_layer.add( self.minimap )
        def update_hud():
            update_labels()
            update_hp_display()
            update_power_display()
            self.minimap.update()
        create_hp_display()
        self.post_physics.add_anonymous_hook( ignore_arguments( update_hud ) )
        self.player.reshape_hooks.add_anonymous_hook( recreate_hp_display )
    def setup_game(self, player_ship_data = None):
        self.sim = physics.PhysicsSimulator( timestep = None )
#        self.player = create_ship_thing( self, self.main_layer, (500,500), shape = "small", hp = 5 )
        if not player_ship_data:
            self.player = Ship.load_file( "current_garage_ship.yaml", self )
        else:
            self.player = Ship.load_data( player_ship_data, self )
        self.player.position = (300,300)
        self.player.invulnerable = False
        self.enemy = create_ship_thing( self, (500,500), shape = "small", hp = 10 )
        self.enemy.invulnerable = False
        self.enemy.body.angular_velocity_limit = degrees_to_radians(144*2)
        self.enemy2 = create_ship_thing( self, (0,500), shape = "small", hp = 10 )
        self.enemy2.invulnerable = False
        self.enemy2.body.angular_velocity_limit = degrees_to_radians(144*2)
        self.enemy.angle_degrees = random.random() * 360.0
        self.enemy2.angle_degrees = random.random() * 360.0
        self.batch = cocos.batch.BatchNode()
        self.main_layer.cocos_layer.add( self.batch )
        self.physics_objects = []
        self.things = []
        self.psys_managed_things = []
        for i in range(200):
            cols = "red", "purple", "grey", "blue", "green", "yellow"
            sq = create_square_thing( self, None, (100,0), None )
            sq.position = (random.random()-0.5) * 4000, (random.random()-0.5) * 4000
            sq.angle_radians = random.random() * math.pi * 2
            sq.mylabel = sq.position
            sq.velocity = (300,10)
            kw = {}
            name = "polygon_normals.4.generated"
            kw[ "size" ] = Vec2d(106.6666666,106.6666666)
            kw[ "texture_coordinates" ] = self.atlas.texcoords( name )
            kw[ "texture_size" ] = self.atlas.texsize( name )
            z = random.random() * 6.28
            r = 0.1 + random.random() * 10.0
            pos = r*math.cos(z), r*math.sin(z)
            # need to translate from pixel space
            # [0,self.
            # to
            # [-1.3333,1.3333] x [-1,1]
            p = sq.position
            p = p + self.main_layer.cocos_layer.position
            p = Vec2d(p) / Vec2d( self.window.width, self.window.height )
            p = (p * 2) - Vec2d(1,1)
            p = p * Vec2d( self.window.width / float(self.window.height), 1 ) 
            kw[ "position" ] = p
            kw[ "angle" ] = sq.angle_radians
            kw[ "colour" ] = 1.0, 0.5, 0.5, 1.0
            index = self.object_psys.add( **kw )
            self.psys_managed_things.append( (sq, index) )
            self.things.append( sq )
        def draw_psys():
            # CMSDTv
            # T = translate by self.main_layer.cocos_layer.position
            # 
            # M = v -> v - (1,1)
            # C = v -> v * (w/h, 1)
            w = float(self.window.width)
            h = float(self.window.height)
            x, y = self.main_layer.cocos_layer.position
            mat = (2.0/w,       0.0,        0.0,        (2*x/w-1),
                   0.0,         2.0/h,      0.0,        (2*y/h-1),
                   0.0,         0.0,        1.0,        0.0,
                   0.0,         0.0,        0.0,        1.0)
            self.object_psys.set_transformation_matrix( mat )
            glEnable( GL_SCISSOR_TEST )
            glScissor( 0, 0, self.window.width + 1 - self.hud_width, self.window.height )
            self.object_psys.draw()
            glDisable( GL_SCISSOR_TEST )
            s = 0.3
            sx, sy = 500 + self.sim._t * 100,200
            sx, sy = self.window.width - self.hud_width * 0.5, self.window.height - self.hud_width * 0.5
            mat = (0.0,         s*2.0/w,    0.0,        (2*sx/w-1),
                   s*2.0/h,     0,          0.0,        (2*sy/h-1),
                   0.0,         0.0,        1.0,        0.0,
                   0.0,         0.0,        0.0,        1.0)
            self.hud_psys.set_transformation_matrix( mat )
            self.hud_psys.draw()
        graphics.Layer( self.scene, cocos_layer = graphics.FunctionCocosLayer( draw_psys ) )
        self.sim.space.add_collision_handler( physics.CollisionTypes["main"], physics.CollisionTypes["bullet"], self.collide_general_with_bullet )
    def setup_input(self):
        input_layer = graphics.Layer( self.scene, gameinput.CocosInputLayer() )
        for k in (key.LEFT, key.RIGHT, key.UP, key.DOWN):
            input_layer.cocos_layer.set_key_hook( k, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_hook( k, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_hook( key.LSHIFT, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_press_hook( key.SPACE, lambda *args, **kwargs: (self.player.on_controls_state(*args,**kwargs), self.shoot_volley(self.player)) )
        input_layer.cocos_layer.set_key_release_hook( key.SPACE, lambda *args, **kwargs: self.player.on_controls_state(*args,**kwargs) )
        input_layer.cocos_layer.set_key_press_hook( key.P, self.on_save_ship )
    def shoot_volley(self, shooter):
        guns = shooter.ready_guns()
        index = 0
        for gun in guns:
            if not gun.may_activate():
                continue
            gun.shoot( shooter )
            gun.activated( index )
    def update_pygame(self):
        self.screen.fill( pygame.color.THECOLORS[ "black" ] )
        draw_space( self.screen, self.sim.space )
        pygame.display.flip()
    def update_psys_managed_objects(self):
        for thing, index in self.psys_managed_things:
            self.object_psys.update_position_and_angle( index, thing.position, thing.angle_radians )
    def collide_general_with_bullet(self, space, arbiter ):
        anything, bullet = arbiter.shapes
        try:
            thing = anything.thing
            index = anything.extra_info
        except AttributeError:
            bullet.thing.ttl = min( bullet.thing.ttl, 0.05 )
            return False
        if bullet.thing.inert:
            return False
        if (bullet.thing.shooter == thing) and bullet.thing.grace > 0.0:
            return False
        try:
            block = thing.block_structure.blocks[ index ]
            hp = block.hp
        except KeyError:
            return False
        except AttributeError:
            return False
        bullet.thing.impact( thing = thing, block_index = index, block = block )
        bullet.thing.inert = True
        bullet.thing.ttl = min( bullet.thing.ttl, 0.05 )
        return False
    def run(self):
        self.window.run( self.scene )
