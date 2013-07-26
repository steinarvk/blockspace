import sys

def include_build_directory():
    sys.path.append( "./build/lib.linux-x86_64-2.7" )

if __name__ == '__main__':
    include_build_directory()
    import bsgl
    bsgl.test()
