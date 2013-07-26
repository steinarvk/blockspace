from distutils.core import setup, Extension

bsgl_module = Extension(
    "bsgl",
    sources = [ "bsglmodule.c", "bsglsystem.c", "cglutil.c" ],
    libraries = ["GL", "glut", "GLEW", "m"],
    extra_compile_args = [ "-std=c99" ]
)

setup( name = "blockspace",
       version = "1.0",
       description = "Blockspace game",
       ext_modules = [ bsgl_module ] )
