from distutils.core import setup, Extension

bsgl_module = Extension( "bsgl", sources = [ "bsglmodule.c" ], libraries = ["GL"] )

setup( name = "blockspace",
       version = "1.0",
       description = "Blockspace game",
       ext_modules = [ bsgl_module ] )
