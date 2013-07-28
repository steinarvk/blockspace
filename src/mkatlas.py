import Image
import yaml

class Rectangle (object):
    def __init__(self, width, height, x = 0, y = 0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def leftmost_pixel(self):
        return self.x

    @property
    def rightmost_pixel(self):
        return self.x + self.width - 1

    @property
    def upper_pixel(self):
        return self.y

    @property
    def lower_pixel(self):
        return self.y + self.height - 1

    def can_contain(self, subrect):
        return self.width >= subrect.width and self.height >= subrect.height
    def area(self):
        return self.width * self.height
    def overlaps(self, rect):
        if self.rightmost_pixel < rect.leftmost_pixel:
            return False
        if self.leftmost_pixel > rect.rightmost_pixel:
            return False
        if self.upper_pixel > rect.lower_pixel:
            return False
        if self.lower_pixel < rect.upper_pixel:
            return False
        return True
    def subtract(self, subrect):
        dw, dh = self.width - subrect.width, self.height - subrect.height
        if dw == 0 and dh == 0:
            return []
        wide_rect = Rectangle( self.width, dh, x = self.x, y = self.y + subrect.height )
        narrow_rect = Rectangle( subrect.width, dh, x = self.x, y = self.y + subrect.height )
        tall_rect = Rectangle( dw, self.height, x = self.x + subrect.width, y = self.y )
        short_rect = Rectangle( dw, subrect.height, x = self.x + subrect.width, y = self.y )
        candidates = [ (wide_rect,short_rect), (narrow_rect,tall_rect) ]
        candidates = map( lambda xs : filter( lambda x : x.area() > 0, xs ), candidates )
#        candidates.sort( key = lambda x : min([min(r.width,r.height) for r in x]) )
        if dw < dh:
            rv = candidates[0]
        else:
            rv = candidates[1]
        return rv

class NotEnoughSpace (Exception):
    pass

class AtlasBuilder (object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.free_rects = [ Rectangle( width, height ) ]
        self.allocated_rects = []
        self.records = {}
        self.image = Image.new( "RGBA", (width, height) )
    def find_free_rect(self, subrect):
        for rect in self.free_rects:
            if rect.can_contain( subrect ):
                return rect
        raise NotEnoughSpace()
    def make_record(self, name, x, y, w, h):
        left, right = x, x + w
        top, bottom = y, y + h
        glx = left / float(self.width)
        gly = bottom / float(self.height)
        glw = w / float(self.width)
        glh = h / float(self.height)
        self.records[ name ] = {"x": glx, "y": gly, "w": glw, "h": glh}
    def split_rect(self, superrect, subrect ):
        new_rects = superrect.subtract( subrect )
        self.free_rects.remove( superrect )
        for new_rect in new_rects:
            assert new_rect.overlaps( superrect )
            for old_rect in self.free_rects:
                assert not new_rect.overlaps( old_rect )
        self.free_rects.extend( new_rects )
        superrect.width, superrect.height = subrect.width, subrect.height
        allocated_rect = superrect
        for previously_allocated_rect in self.allocated_rects:
            assert not previously_allocated_rect.overlaps( allocated_rect )
        self.allocated_rects.append( allocated_rect )
    def pack(self, name, subrect, blitter):
        superrect = self.find_free_rect( subrect )
        self.split_rect( superrect, subrect )
        x, y = superrect.x, superrect.y
        w, h = subrect.width, subrect.height
        self.make_record( name, x, y, w, h )
        blitter( self.image, x, y )
    def pack_many(self, triples):
        triples.sort( reverse = True, key = lambda tu: max(tu[1].width, tu[1].height) )
        for triple in triples:
            self.pack( *triple )
    def save(self, atlas_name):
        self.image.save( atlas_name + ".png" )
        with open( atlas_name + ".yaml", "w" ) as f:
            f.write( yaml.safe_dump( self.records ) )

def rect_from_image( image_name ):
    img = Image.open( image_name )
    return Rectangle( *img.size )

def blit_image( canvas, image_name, x, y, w, h ):
    img = Image.open( image_name )
    box = (x, y, x+w, y+h)
    canvas.paste( img, box )

def scale_list( l, n ):
    rv = []
    full_cycles = int(n)
    for i in range(int(n)):
        rv.extend( l )
    for i in range(int((n-int(n)) * len(l))):
        rv.append( l[i] )
    return rv

def filename_to_element_name( fn ):
    import os
    return os.path.splitext( os.path.basename(fn) )[0]

def main_test_fill_sheet():
    import sys
    entries = []
    def create_blitter( fn, sz ):
        return lambda canvas, x, y : blit_image( canvas, fn, x, y, sz.width, sz.height )
    for fn in sys.argv[1:]:
        sz = rect_from_image( fn )
        entries.append( (filename_to_element_name(fn), sz, create_blitter(fn,sz) ) )
    def attempt_to_fill( fn, l ):
        atlas = AtlasBuilder(2048,2048)
        atlas.pack_many( scale_list( l, sc ) )
        atlas.save( fn )
    minsc = 0.001
    maxsc = 10.0
    for i in range(20):
        sc = (minsc+maxsc)*0.5
        l = scale_list( entries, sc )
        print "trying", len(l)
        try:
            attempt_to_fill( "atlas.generated", l )
            minsc = sc
        except NotEnoughSpace:
            maxsc = sc

def main_make_fixed_sheet( sheetsize = 1024 ):
    entries = []
    def create_blitter( fn, sz ):
        return lambda canvas, x, y : blit_image( canvas, fn, x, y, sz.width, sz.height )
    for n in (3,4,5,6,8):
        fn = "polygon_normals.{}.generated.png".format( n )
        en = "polygon-{}".format( n )
        sz = rect_from_image( fn )
        entries.append( (en, sz, create_blitter(fn, sz)) )
    atlas = AtlasBuilder(sheetsize,sheetsize)
    atlas.pack_many( entries )
    atlas.save( "atlas.generated" )

def main_make_sheet_from_files( sheetsize = 1024):
    import sys
    entries = []
    def create_blitter( fn, sz ):
        return lambda canvas, x, y : blit_image( canvas, fn, x, y, sz.width, sz.height )
    for fn in sys.argv[1:]:
        sz = rect_from_image( fn )
        entries.append( (filename_to_element_name(fn), sz, create_blitter(fn,sz) ) )
    atlas = AtlasBuilder(sheetsize,sheetsize)
    atlas.pack_many( entries )
    atlas.save( "atlas.generated" )

if __name__ == '__main__':
    main_make_sheet_from_files()
