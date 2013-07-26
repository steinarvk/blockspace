#include <Python.h>

static PyObject *bsgl_test(PyObject *self, PyObject *args) {
    fprintf(stderr, "Hello world!\n" );
    Py_INCREF( Py_None );
    return Py_None;
}

static PyMethodDef BsGLMethods[] = {
    { "test", bsgl_test, METH_VARARGS, "Print a test message." },
    { NULL, NULL, 0, NULL }
};

PyMODINIT_FUNC initbsgl(void) {
    Py_InitModule( "bsgl", BsGLMethods );

    fprintf( stderr, "BSGL module initialized.\n" );
}
