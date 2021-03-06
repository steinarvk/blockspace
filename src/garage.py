import graphics
import blocks
import cocos
import gameinput
import physics
import component
from component import create_component

from atlas import Atlas
from pyglet.gl import *

from bsc import include_build_directory
include_build_directory()

import bsgl

from blocks import PolygonBlock

from world import World
from gameinput import key, mouse
from game import create_ship_thing

from util import *

from ship import Ship

import sys

def decorate_block_with_engines_within( block, aim = 180.0, span = 120.0, align = False ):
    for index, edge in indexed_zip( block.edges ):
        angle = edge.angle_degrees - block.rotation_degrees
        angle_error = (((edge.angle_degrees - aim + 180.0) % 360.0) - 180.0) / (span * 0.5)
        point = edge.midpoint() - block.translation
        if abs(angle_error) < 1.001:
            if align:
                angle = aim - block.rotation_degrees
            context = { "block": block }
            engine = create_component( "engine", context, position = tuple(point), angle_degrees = angle, required_edge = index, power = 500, cost = 50 )
    return block

def decorate_block_with_guns_within( block, aim = 0.0, span = 120.0, align = False ):
    for index, edge in indexed_zip( block.edges ):
        angle = edge.angle_degrees - block.rotation_degrees
        angle_error = (((edge.angle_degrees - aim + 180.0) % 360.0) - 180.0) / (span * 0.5)
        point = edge.midpoint() - block.translation
        if abs(angle_error) < 1.001:
            if align:
                angle = aim - block.rotation_degrees
            cooldown = 0.2
            cost = (750 * cooldown) * 2.0/3.0 # more reasonable power usage
            context = { "block": block }
            gun = create_component( "missile-launcher", context, position = tuple(point), angle_degrees = angle, required_edge = index, cooldown = cooldown, cost = cost)
    return block

def decorate_block_normal( block ):
    block.role = "plain"
    block.colour = (255,255,255)
    return block

def decorate_block_cockpit( block ):
    block.role = "cockpit"
    block.colour = (0,255,0)
    block.cockpit = True
    context = { "block": block }
    create_component( "generator", context, production = int(0.5 + 0.5 * block.area()) )
    create_component( "battery", context, storage = int(0.5 + 0.5 * block.area()) )
    return block

def decorate_block_battery( block ):
    block.role = "battery"
    block.colour = (255,255,0)
    context = { "block": block }
    create_component( "battery", context, storage = block.area() )
    return block

def decorate_block_generator( block ):
    block.role = "generator"
    block.colour = (255,0,0)
    context = { "block": block }
    create_component( "generator", context, production = int(0.5 + 0.5 * block.area()) )
    return block

def decorate_block_armour( block ):
    block.role = "armour"
    block.colour = (64,64,64)
    block.hp *= 3
    return block

class GarageWorld (World):
    def __init__(self, window, continuation_with_ship = None, **kwargs):
        super( GarageWorld, self ).__init__( **kwargs )
        self.window = window
        self.scene = graphics.Scene( self.window )
        self.sim = physics.PhysicsSimulator( timestep = None )
        self.input_layer = gameinput.CocosInputLayer()
        layer = graphics.Layer( self.scene, cocos.layer.ColorLayer(128,0,128,255) )
        graphics.Layer( self.scene, cocos_layer = graphics.FunctionCocosLayer( self.draw_psys ) )
        layer.cocos_layer.position = 0,0
        graphics.Layer( self.scene, self.input_layer )
        self.atlas = Atlas( "atlas.generated" )
        self.object_psys = bsgl.System( texture_id = self.atlas.sheet.get_texture().id )
        self.input_layer.mouse_motion_hooks.append( self.on_mouse_motion )
        self.main_layer = graphics.Layer( self.scene )
        self.root_node = cocos.cocosnode.CocosNode()
        self.main_layer.cocos_layer.add( self.root_node )
        self.continuation_with_ship = continuation_with_ship
        root = PolygonBlock.load_file( "blocks/poly5.yaml" )
        self.root_node.scale = 1
#        for i in range(7):
#            a = s.attach((0,i), blocks.QuadBlock(32), 0)
#            b = s.attach((a,2), blocks.QuadBlock(32), 0)
#            c = s.attach((b,2), blocks.QuadBlock(32), 0)
#            d = s.attach((c,1), blocks.QuadBlock(32), 3)
#        self.sprite_structure = None
        self.garage_ship = None
        self.block_shapes = map( lambda n : (lambda : PolygonBlock.load_file( "blocks/poly{}.yaml".format(n) )), (3,4,5,6,8) )
        self.block_decorators = [ decorate_block_armour, decorate_block_battery, decorate_block_generator ]
        self.block_gun_mounter = decorate_block_with_guns_within
        self.block_engine_mounter = decorate_block_with_engines_within
        self.current_block_shape = self.block_shapes[0]
        self.current_block_decorator = self.block_decorators[0]
        self.restart_block_structure()
        self.mouse_index = None
        self.current_rotation = 0.0
        self.current_position = (0,0)
        self.set_current_block()
        self.input_layer.mouse_scroll_hooks.add_anonymous_hook( self.on_mouse_scroll )
        if self.continuation_with_ship:
            self.input_layer.set_key_press_hook( key.ENTER, self.on_continue_with_ship )
        self.input_layer.set_key_press_hook( key.SPACE, self.on_place_block )
        self.input_layer.set_key_press_hook( key.UP, self.on_next_shape )
        self.input_layer.set_key_press_hook( key.DOWN, self.on_previous_shape )
        self.input_layer.set_key_press_hook( key.RIGHT, self.on_next_decorator )
        self.input_layer.set_key_press_hook( key.LEFT, self.on_previous_decorator )
        self.input_layer.set_key_press_hook( key.R, self.on_restart_with_current )
        self.input_layer.set_key_press_hook( key.P, self.on_save_ship )
        self.input_layer.set_key_press_hook( key.L, self.on_load_ship )
        self.input_layer.mouse_press_hooks[ mouse.RIGHT ] = self.on_next_shape
        self.input_layer.mouse_press_hooks[ mouse.LEFT ] = self.on_place_block
        self.refresh_garage_ship()
        self.physics.add_anonymous_hook( self.sim.tick )
        self.idle_time = 0.0
        self.currently_idle = False
    def on_continue_with_ship(self, *args, **kwargs):
        self.continuation_with_ship( self.garage_ship )
    def draw_psys(self):
        w = float(self.window.width)
        h = float(self.window.height)
        x, y = self.main_layer.cocos_layer.position
        mat = (2.0/w,       0.0,        0.0,        (2*x/w-1),
               0.0,         2.0/h,      0.0,        (2*y/h-1),
               0.0,         0.0,        1.0,        0.0,
               0.0,         0.0,        0.0,        1.0)
        self.object_psys.set_transformation_matrix( mat )
        self.object_psys.draw()
    def on_restart_with_current(self, *args):
        self.reset_idle_time()
        self.restart_block_structure()
    def restart_block_structure(self, root = None):
        if not root:
            root = self.current_block_shape()
        root = decorate_block_cockpit( root )
        root = decorate_block_with_guns_within( root )
        root = decorate_block_with_engines_within( root )
        self.block_structure = blocks.BlockStructure( root )
        self.refresh_garage_ship()
    def refresh_garage_ship(self):
        self.block_structure.zero_centroid()
        if self.garage_ship:
            self.garage_ship.kill()
        self.garage_ship = Ship( self, self.block_structure, (0,0), cocos_parent = self.root_node )
#        self.pre_physics.add_hook( self.garage_ship, self.garage_ship.update )
        self.scene.schedule( self.update_everything )
    def start_idle_animation(self):
        self.currently_idle = True
        # how come angular velocity below 1 radian fails?
    def stop_idle_animation(self):
        self.garage_ship.body.angular_velocity = 0
        self.garage_ship.body.angle = 0
        self.currently_idle = False
    def update_everything(self, dt):
        self.garage_ship.sprite.update_elements()
        if self.currently_idle:
            self.garage_ship.body.angular_velocity = degrees_to_radians( 360.0 / 10.0 )
        self.tick( dt )
        self.display_update()
        if not self.currently_idle:
            self.idle_time += dt
            if self.idle_time > 5.0:
                self.start_idle_animation()
    def reset_idle_time(self):
        self.idle_time = 0.0
        if self.currently_idle:
            self.stop_idle_animation()
    def on_place_block(self, *args):
        self.reset_idle_time()
        args = self.check_borders()
        if args:
            self.attach_current_block( *args )
    def create_block(self):
        block = self.current_block_shape()
        block = self.current_block_decorator( block )
        return block
    def decorate_attached_block(self, block):
        self.block_gun_mounter( block )
        self.block_engine_mounter( block )
    def check_borders(self):
        block = self.create_block()
        block.rotate_degrees( self.current_rotation )
        block.translate( self.current_position )
        for index in self.block_structure.free_edge_indices:
            edge = self.block_structure.edge( index )
        for local_edge_index in block.free_edge_indices:
            local_edge = block.edge( local_edge_index )
            for index in self.block_structure.free_edge_indices:
                edge = self.block_structure.edge( index )
                if local_edge.almost_overlaps( edge, max_distance = 5 ):
                    return (local_edge_index, index)
        return None
    def attach_current_block(self, current_block_edge_index, structure_edge_index ):
        try:
            block = self.create_block()
            self.block_structure.attach( structure_edge_index, block, current_block_edge_index )
            self.decorate_attached_block( block )
            self.refresh_garage_ship()
        except blocks.IllegalOverlapException:
            print "overlap"
    def set_current_block(self, shape = None, decorator = None):
        if shape:
            self.current_block_shape = shape
        if decorator:
            self.current_block_decorator = decorator
        if self.mouse_index != None:
            self.object_psys.remove( self.mouse_index )
        block = self.create_block()
        info = block.create_sheet_info( self.atlas )
        info[ "position" ] = (0,0)
        info[ "angle" ] = 0.0
        self.mouse_index = self.object_psys.add( **info )
        self.refresh_mouse_sprite()
    def change_block_shape(self, delta = 1):
        self.set_current_block(shape = self.block_shapes[ (self.block_shapes.index( self.current_block_shape ) + delta) % len( self.block_shapes )])
    def change_block_decorator(self, delta = 1):
        self.set_current_block(decorator = self.block_decorators[ (self.block_decorators.index( self.current_block_decorator ) + delta) % len( self.block_decorators )])
    def on_next_decorator(self, *args):
        self.reset_idle_time()
        self.change_block_decorator( 1 )
    def on_previous_decorator(self, *args):
        self.reset_idle_time()
        self.change_block_decorator( -1 )
    def on_next_shape(self, *args):
        self.reset_idle_time()
        self.change_block_shape( 1 )
    def on_previous_shape(self, *args):
        self.reset_idle_time()
        self.change_block_shape( -1 )
    def refresh_mouse_sprite(self):
        if self.mouse_index != None:
            self.object_psys.update_position_and_angle( self.mouse_index, self.current_position, degrees_to_radians( self.current_rotation ) )
    def rotate_sprite(self, taps = 1):
        tap_size = 10
        self.current_rotation = (self.current_rotation + taps * tap_size) % 360.0
        self.refresh_mouse_sprite()
    def on_mouse_scroll(self, x, y, sx, sy):
        self.reset_idle_time()
        self.rotate_sprite( -sy )
    def on_mouse_motion(self, x, y, dx, dy):
        self.reset_idle_time()
        self.current_position = self.root_node.point_to_local( (x,y) )
        self.refresh_mouse_sprite()
    def on_load_ship(self, *args):
        self.reset_idle_time()
        self.garage_ship.kill()
        ship = Ship.load_file( "current_garage_ship.yaml", self, cocos_parent = self.root_node )
        self.block_structure = ship.block_structure
        self.refresh_garage_ship()
        ship.kill()
    def on_save_ship(self, *args):
        self.reset_idle_time()
        s = self.garage_ship.dump_string()
        print >> sys.stderr, s
        self.garage_ship.dump_file( "current_garage_ship.yaml" )
    def run(self):
        self.window.run( self.scene )

if __name__ == '__main__':
    window = graphics.Window()
    def continue_with_ship( ship ):
        import game
        game.MainWorld( window, player_ship_data = ship.dump_data() ).run()
    GarageWorld( window, continuation_with_ship = continue_with_ship ).run()
