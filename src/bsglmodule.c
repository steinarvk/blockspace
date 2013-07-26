#include <Python.h>

#include <GL/gl.h>

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

    fprintf( stderr, "BSGL module initialized.\n" );
}
