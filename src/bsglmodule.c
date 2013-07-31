#include <Python.h>

#include <GL/glew.h>

#include <math.h>

#include "bsglsystem.h"

static PyMethodDef BsGLMethods[] = {
    { NULL, NULL, 0, NULL }
};

PyMODINIT_FUNC initbsgl(void) {
    if( PyType_Ready( &SystemType ) < 0 ) {
        fprintf( stderr, "BSGL module initialization failed!\n");
        return;
    }

    PyObject *m = Py_InitModule( "bsgl", BsGLMethods );

    Py_INCREF( & SystemType );
    PyModule_AddObject( m, "System", (PyObject*) &SystemType );

    GLenum err = glewInit();
    if( err != GLEW_OK ) {
        fprintf( stderr, "GLEW initialization failed!\n" );
        fprintf( stderr, "%d\n", err );
    }

    if( !GLEW_VERSION_2_1 ) {
        fprintf( stderr, "OpenGL 2.1 not supported!\n" );
    }

    srand( time(NULL) );

    fprintf( stderr, "BSGL module initialized.\n" );
}
