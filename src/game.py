import graphics
import physics
import gameinput
import ai

from physics import ConvexPolygonShape, DiskShape, Vec2d
from gameinput import key

import cocos

import random

from util import *

from pyglet.gl import *

from functools import partial
from itertools import cycle

import pygame
from pymunk.pygame_util import draw_space
import pymunk

import blocks
import component

from operator import attrgetter

from world import World

from ship import Ship, Debris

collision_type_main = 1
collision_type_bullet = 2
group_bulletgroup = 1

def with_engine( block, edge_index = 3, sprite = None ):
    try:
        rv = block
        for index in edge_index:
            rv = with_engine( rv, index, sprite = sprite )
        return rv
    except TypeError:
        pass
    angle = block.edge( edge_index ).angle_degrees
    pos = Vec2d( polar_degrees( angle, 16.0 ) )
    pos = Vec2d(0,0)
    pos = block.edge( edge_index ).midpoint()
    spr = cocos.sprite.Sprite( sprite )
    spr.scale = 0.15
    engine = component.EngineComponent( 500, block, pos, angle, required_edges = (edge_index,), category = "engine", sprite = spr )
    engine.power_usage = 50
    return block

def with_gun( block, edge_index = 1, sprite = None ):
    try:
        rv = block
        for index in edge_index:
            rv = with_gun( rv, index, sprite = sprite )
        return rv
    except TypeError:
        pass
    angle = block.edge( edge_index ).angle_degrees
    pos = Vec2d( polar_degrees( angle, 16.0 ) )
    pos = Vec2d(0,0)
    pos = block.edge( edge_index ).midpoint()
    spr = cocos.sprite.Sprite( sprite )
    spr.scale = 0.15
    gun = component.PointComponent( block, pos, angle, required_edges = (edge_index,), category = "gun", sprite = spr )
    gun.cooldown = 0.2
#    gun.cooldown = 0.1 # a LOT more powerful with lower cooldown
    gun.power_usage = (750 * gun.cooldown) * 2.0/3.0 # more reasonable power usage
    return block

def with_guns( block, sprite = None ):
    return with_gun( block, range(len(block.edges)), sprite = sprite )
        
def create_ship_thing(world, layer, position, shape = "small", hp = 1, recolour = True):
    gun_img = world.gem_images[10]
    engine_img = world.gem_images[14]
    def w_engine( b, edge_index = (3)):
        return with_engine( b, edge_index = edge_index, sprite = engine_img )
    def w_cockpit( b ):
        return b
    def w_gun( b, edge_index = 1 ):
        return with_gun( b, edge_index = edge_index, sprite = gun_img )
    def w_guns( b ):
        return with_guns( b, sprite = gun_img )
    def quad_block():
        good_block = blocks.QuadBlock(32)
        bad_block = blocks.PolygonBlock.load_file( "blocks/poly4.yaml" )
        print "good", good_block.dump_data()
        print "bad", bad_block.dump_data()
        return blocks.QuadBlock(32)
        return blocks.PolygonBlock.load_file( "blocks/poly4.yaml" )
    def octa_block():
        return blocks.OctaBlock(32)
        return blocks.PolygonBlock.load_file( "blocks/poly8.yaml" )
    # 2
    #3 1
    # 0
    if shape == "small":
        s = blocks.BlockStructure( w_engine(w_gun(w_cockpit(quad_block()))) )
        s.attach((0,2), w_engine(w_gun(quad_block())), 0)
        s.attach((0,0), w_engine(w_gun(quad_block())), 2)
        s.attach((0,1), w_engine(w_gun(quad_block())), 3)
    elif shape == "big":
        s = blocks.BlockStructure( w_engine(w_cockpit(quad_block())) )
        s.attach((0,2), w_engine(quad_block()), 0)
        s.attach((0,0), w_engine(quad_block()), 2)
        s.attach((0,1), w_engine(quad_block()), 3)
        s.attach((3,2), w_engine(quad_block()), 0)
        s.attach((3,0), w_engine(quad_block()), 2)
        s.attach((3,1), w_engine(w_gun(quad_block(), 1)), 3)
    elif shape == "bigger":
        s = blocks.BlockStructure( w_gun(w_engine(quad_block())) )
        s.attach((0,2), w_gun(w_engine(quad_block())), 0)
        s.attach((0,0), w_gun(w_engine(quad_block())), 2)
        s.attach((0,1), w_gun(w_engine(quad_block())), 3)
        s.attach((3,2), w_gun(w_engine(quad_block())), 0)
        s.attach((3,0), w_gun(w_engine(quad_block())), 2)
        s.attach((3,1), w_gun(w_engine(quad_block())), 3)
        s.attach((6,2), w_gun(w_engine(quad_block())), 0)
        s.attach((6,0), w_gun(w_engine(quad_block())), 2)
        s.attach((6,1), w_gun(w_engine(quad_block())), 3)
    elif shape == "single_weird":
        s = blocks.BlockStructure( w_gun(w_engine(blocks.PolygonBlock.load_file( "blocks/poly5.yaml" ) ) ) )
    elif shape == "single":
        s = blocks.BlockStructure( w_guns( w_cockpit( quad_block() ) ) )
    elif shape == "octa":
        s = blocks.BlockStructure( w_guns( w_cockpit( octa_block() ) ) )
        for i in range(7):
            a = s.attach((0,i), quad_block(), 0)
            b = s.attach((a,2), quad_block(), 0)
            c = s.attach((b,2), quad_block(), 0)
            d = s.attach((c,1), w_gun(quad_block(), 1), 3)
    elif shape == "wide":
        s = blocks.BlockStructure( w_guns(w_engine( quad_block() )) )
        s.attach((0,1), w_engine(w_guns(quad_block())), 3)
        l, r = 0, 0
        for i in range(6):
            l = s.attach((l,2), w_guns(w_engine(quad_block())), 0)
            r = s.attach((r,0), w_guns(w_engine(quad_block())), 2)
        l = s.attach((l,2), w_guns(w_engine(quad_block())), 0)
        r = s.attach((r,0), w_guns(w_engine(quad_block())), 2)
    elif shape == "long":
        s = blocks.BlockStructure( w_cockpit( quad_block() ) )
        l, r = 0, 0
        for i in range(6):
            l = s.attach((l,3), w_guns(quad_block()), 1)
            r = s.attach((r,1), w_guns(quad_block()), 3)
    else:
        s = shape
    s.zero_centroid()
    print "ship with", len(s.blocks), "blocks has", len(s.free_edge_indices)
    if recolour:
        colours = { "blue": (0,0,255),
                    "purple": (255,0,255),
                    "white": (255,255,255),
                    "green": (0,255,0),
                    "yellow": (255,255,0),
                    "dark-gray": (64,64,64),
                    "red": (255,0,0) }
        def make_cockpit( block ):
            cockpit = component.Component( block, categories = ("generator","battery") )
            cockpit.power_capacity = int(0.5 + 0.5 * block.area())
            cockpit.power_production = int(0.5 + 0.5 * block.area())
            block.max_hp = block.hp = hp * 3
            block.colour = colours["green"]
            block.cockpit = True
        def make_battery( block ):
            battery = component.Component( block, categories = ("battery") )
            battery.power_capacity = int(block.area())
            block.colour = colours["yellow"]
        def make_generator( block ):
            generator = component.Component( block, categories = ("generator") )
            generator.power_production = int(0.5 + 0.5 * block.area())
            block.colour = colours["red"]
        def make_armour( block ):
            block.max_hp = block.hp = hp * 5
            block.colour = colours["dark-gray"]
        gens = make_battery, make_generator, make_armour
        gens = (make_armour,)
        for block in s.blocks:
            block.max_hp = block.hp = hp
            block.cockpit = False
        for block in list(s.blocks)[1:]:
            random.choice(gens)( block )
        make_cockpit( s.blocks[0] )
    rv = Ship( world, s, position, layer = layer, mass = len(s.blocks), moment = 20000.0, collision_type = collision_type_main )
    rv._gun_distance = 65
    return rv

def create_square_thing(world, layer, position, image):
    points = [(0,0),(32,0),(32,32),(0,32)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
    moment = pymunk.moment_for_poly( 1.0, shape.vertices )
    rv = Debris( world, layer, position, shape, image, moment = moment, collision_type = collision_type_main )
    return rv

def create_bullet_thing(world, image, shooter, gun):
    points = [(0,0),(9,0),(9,33),(0,33)]
    shape = ConvexPolygonShape(*points)
    shape.translate( shape.centroid() * -1)
#    shape = DiskShape(5) # useful for debugging with pygame to see bullet origins
    layer = None
    rv = Debris( world, layer, (0,0), shape, image, mass = 1.0, moment = physics.infinity, collision_type = collision_type_bullet, group = group_bulletgroup )
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
    return rv

class MainWorld (World):
    def __init__(self, resolution = (1000,800), use_pygame = False, **kwargs):
        super( MainWorld, self ).__init__( **kwargs)
        self.setup_graphics( resolution )
        self.setup_game()
        self.setup_input()
        self.setup_hud()
        self.camera.following = self.player
        self.main_layer.camera = self.camera
        if use_pygame:
            self.setup_pygame( resolution )
            self.display.add_anonymous_hook( self.update_pygame )
        self.pre_display.add_anonymous_hook( self.update_display_objects )
        self.pre_physics.add_anonymous_hook( self.update_camera )
        self.display.add_anonymous_hook( self.scene.update )
        self.player.body.velocity_limit = 800.0 # experiment with this for actually chasing fleeing ships
        self.pre_physics.add_hook( self.player, self.player.update )
        self.pre_physics.add_hook( self.enemy, lambda dt : ai.ai_seek_target( dt, self.enemy, self.player, partial( self.shoot_bullet, self.enemy ) ) )
#        self.pre_physics.add_hook( self.enemy, lambda dt : ai.ai_flee_target( dt, self.enemy, self.player ) )
        self.pre_physics.add_hook( self.enemy, self.enemy.update )
        self.pre_physics.add_hook( self.enemy2, lambda dt : ai.ai_seek_target( dt, self.enemy2, self.player, partial( self.shoot_bullet, self.enemy2 ) ) )
#        self.pre_physics.add_hook( self.enemy2, lambda dt : ai.ai_flee_target( dt, self.enemy2, self.player ) )
        self.pre_physics.add_hook( self.enemy2, self.enemy2.update )
        for gun in self.player.block_structure.get_components( lambda x : "gun" in x.categories ):
            gun.cooldown /= 2.0
        for x in (self.player, self.enemy, self.enemy2):
            self.post_physics.add_hook( x, x.tick )
            x.add_to_minimap( self.minimap, "solid_white_5x5.png", (0,255,0) if x == self.player else (255,0,0) )
#        for x in self.things:
#            x.add_to_minimap( self.minimap, "solid_white_5x5.png", (128,128,128) )
        self.physics.add_anonymous_hook( self.sim.tick )
        self.scene.schedule( self.update_everything )
    def update_everything(self, dt):
        self.tick( dt )
        self.display_update()
    def update_camera(self, dt):
        self.camera.update( dt )
    def setup_pygame(self, resolution):
        pygame.init()
        self.screen = pygame.display.set_mode( resolution )
    def setup_graphics(self, resolution):
        self.window = graphics.Window( resolution )
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
    def setup_hud(self):
        def update_hp_display():
            undamaged = 255,255,255
            undamaged_cockpit = 0,255,0
            damaged = damaged_cockpit = 255,0,0
            for block, sprite in self.hud_sprite.subcomponent.items():
                rel = float(block.hp) / block.max_hp
                a = damaged_cockpit if block.cockpit else damaged
                b = undamaged_cockpit if block.cockpit else undamaged
                sprite.color = vector_lerp( rel, a, b )
                cockpit = False
        def create_hp_display():
            self.hud_sprite = self.player.block_structure.create_sprite_structure( layer = self.hud_layer )
            expected_size = self.hud_width
            self.hud_sprite.node.position = self.window.width - expected_size*0.5, self.window.height - expected_size * 0.5
            self.hud_sprite.node.rotation = -90.0
            self.hud_sprite.node.scale = 0.5
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
            number_of_guns_label.element.text = "#E: {0}/{1}".format( len( self.player.ready_guns() ), len( self.player.all_guns() ) )
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
    def setup_game(self):
        self.sim = physics.PhysicsSimulator( timestep = None )
        self.player = create_ship_thing( self, self.main_layer, (500,500), shape = "small", hp = 5 )
#        self.player = Ship.load_file( "current_garage_ship.yaml", self, layer = self.main_layer )
        self.player.position = (300,300)
        self.player.invulnerable = False
        self.enemy = create_ship_thing( self, self.main_layer, (500,500), shape = "small", hp = 0 )
        self.enemy.invulnerable = False
        self.enemy.body.angular_velocity_limit = degrees_to_radians(144*2)
        self.enemy2 = create_ship_thing( self, self.main_layer, (0,500), shape = "small", hp = 0 )
        self.enemy2.invulnerable = False
        self.enemy2.body.angular_velocity_limit = degrees_to_radians(144*2)
        self.enemy.angle_degrees = random.random() * 360.0
        self.enemy2.angle_degrees = random.random() * 360.0
        self.img_square = pyglet.image.load( "myblockgray.png" )
        self.img_bullet = pyglet.image.load( "laserGreen.png" )
        self.batch = cocos.batch.BatchNode()
        self.main_layer.cocos_layer.add( self.batch )
        self.display_objects = []
        self.physics_objects = []
        self.things = []
        for i in range(200):
            cols = "red", "purple", "grey", "blue", "green", "yellow"
            sq = create_square_thing( self, None, (100,0), self.img_square )
            sq.position = (random.random()-0.5) * 4000, (random.random()-0.5) * 4000
            sq.angle_radians = random.random() * math.pi * 2
            sq.mylabel = sq.position
            sq.velocity = (300,10)
            self.batch.add( sq.sprite.cocos_sprite )
            self.display_objects.append( sq.sprite )
            self.things.append( sq )
        self.sim.space.add_collision_handler( collision_type_main, collision_type_bullet, self.collide_general_with_bullet )
    def setup_input(self):
        input_layer = graphics.Layer( self.scene, gameinput.CocosInputLayer() )
        for k in (key.LEFT, key.RIGHT, key.UP, key.DOWN):
            input_layer.cocos_layer.set_key_hook( k, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_hook( k, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_hook( key.LSHIFT, self.player.on_controls_state )
        input_layer.cocos_layer.set_key_press_hook( key.SPACE, lambda *args, **kwargs: (self.player.on_controls_state(*args,**kwargs), self.shoot_bullet(self.player)) )
        input_layer.cocos_layer.set_key_release_hook( key.SPACE, lambda *args, **kwargs: self.player.on_controls_state(*args,**kwargs) )
    def shoot_bullet(self, shooter):
        guns = shooter.ready_guns()
        index = 0
        for gun in guns:
            if not gun.may_activate():
                continue
            gun.activated( index )
            sq = create_bullet_thing( self, self.img_bullet, shooter, gun )
            def update_bullet( bullet, dt ):
                if not bullet.alive:
                    return
                bullet.ttl -= dt
                bullet.grace -= dt
                if bullet.ttl <= 0.0:
                    bullet.kill()
            def kill_bullet( sq ):
                self.display_objects.remove( sq.sprite )
                if sq.sprite.cocos_sprite in self.batch:
                    self.batch.remove( sq.sprite.cocos_sprite )
            sq.ttl = 1.5
            self.display_objects.append( sq.sprite )
            self.batch.add( sq.sprite.cocos_sprite )
            sq.kill_hooks.append( kill_bullet )
            self.pre_physics.add_hook( sq, partial(update_bullet,sq) )
            index += 1
    def update_pygame(self):
        self.screen.fill( pygame.color.THECOLORS[ "black" ] )
        draw_space( self.screen, self.sim.space )
        pygame.display.flip()
    def update_display_objects(self):
        x, y = self.camera.focus
        hw, hh = 0.5 * self.window.width, 0.5 * self.window.height
        screen_slack = 100.0
        beyond_slack = screen_slack + 500.0
        screen_bb = pymunk.BB(x-hw-screen_slack,y-hh-screen_slack,x+hw+screen_slack,y+hh+screen_slack)
        big_bb = pymunk.BB(x-hw-beyond_slack,y-hh-beyond_slack,x+hw+beyond_slack,y+hh+beyond_slack)
        onscreen = set(self.sim.space.bb_query( screen_bb ))
        for shape in onscreen:
            shape.thing.sprite.update()
        prech = set(self.batch.get_children())
        for spr in self.display_objects:
            if all((shape not in onscreen for shape in spr.thing.shapes)):
                if spr.cocos_sprite in prech:
                    self.batch.remove( spr.cocos_sprite )
            else:
                if spr.cocos_sprite not in prech:
                    self.batch.add( spr.cocos_sprite )
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
        if not thing.invulnerable:
            block.hp = hp - 1
            if block.hp <= 0:
                detached_block = thing.block_structure.remove_block( index )
                detached_block.detach_components( thing )
                detachable_blocks = []
                detached_parts = []
                if index == 0:
                    survivor = None
                    for index, block in thing.block_structure.blocks.indexed():
                            if index != 0:
                                detachable_blocks.append( index )
                else:
                    survivor = thing.block_structure.any_block_index()
                    if survivor != None:
                        survivors = thing.block_structure.connectivity_set_of( survivor )
                        for index, block in thing.block_structure.blocks.indexed():
                            if index not in survivors:
                                detachable_blocks.append( index )
                while detachable_blocks:
                    x = thing.block_structure.connectivity_set_of( detachable_blocks.pop(0) )
                    detached_parts.append( x )
                    detachable_blocks = filter( lambda z : z not in x, detachable_blocks )
                def on_detached_single_block( detached_block ):
                    vel = detached_block.velocity
                    deg = detached_block.angle_degrees
                    pos = detached_block.position
                    r, g, b = detached_block.colour
                    tr,tg,tb = 0.5,0.5,0.75
                    detached_block.colour = int(r*tr),int(g*tg),int(b*tb)
                    def create_later():
                        debris = create_ship_thing( self, self.main_layer, pos, shape = blocks.BlockStructure( detached_block ), recolour = False )
                        debris.angle_degrees = deg
                        debris.velocity = vel
                    self.queue_once( create_later )
                on_detached_single_block( detached_block )
                for detached_part in detached_parts:
                    # this must be amended to reconstruct the connections
                    for index in detached_part:
                        db = thing.block_structure.remove_block( index )
                        db.detach_components( thing )
                        on_detached_single_block( db )
                if survivor != None:
                    remaining_block = thing.block_structure.blocks[survivor]
                    wpv = [(1,b.position-thing.position,b.velocity) for b in thing.block_structure.blocks ]
                    pos_before = remaining_block.position
                    angle_before = remaining_block.angle_degrees
                    thing.block_structure.zero_centroid()
                    thing.block_structure.clear_collision_shape()
                    thing.reshape( thing.block_structure.create_collision_shape() )
                    pos_after = remaining_block.position
                    angle_after = remaining_block.angle_degrees
                    thing.position -= (pos_after - pos_before)
                    linear, rotational = physics.calculate_velocities( wpv )
                    thing.velocity = linear
                    thing.angular_velocity = rotational
                    pos_after = remaining_block.position
                    angle_after = remaining_block.angle_degrees
                    assert degrees_almost_equal( angle_after, angle_before )
                    assert vectors_almost_equal( pos_before, pos_after )
                density = 1/1024.
                area = thing.block_structure.area()
                mass = density * area
                if mass > 0:
                    thing.mass = mass
        if len(thing.block_structure.blocks) == 0:
            thing.kill()
        bullet.thing.inert = True
        bullet.thing.ttl = min( bullet.thing.ttl, 0.05 )
        return False
    def run(self):
        self.window.run( self.scene )

if __name__ == '__main__':
    MainWorld().run()
