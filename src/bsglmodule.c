#include <Python.h>

#include <GL/gl.h>

static PyObject *bsgl_test(PyObject *self, PyObject *args) {
    float offset_x = 300.0, offset_y = 200.0;
    float sz = 100.0;

    glLoadIdentity();                                   // Reset The Current Modelview Matrix
    glColor3f(0.5f,0.5f,1.0f);                          // Set The Color To Blue One Time Only
    glBegin(GL_QUADS);                                  // Draw A Quad
        glVertex2f( offset_x, offset_y + sz );
        glVertex2f( offset_x + sz, offset_y + sz );
        glVertex2f( offset_x + sz, offset_y );
        glVertex2f( offset_x, offset_y );
    glEnd();                                            // Done Drawing The Quad

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
