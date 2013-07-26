#include <Python.h>

#include <GL/gl.h>

#include <math.h>

static PyObject *bsgl_initialize(PyObject *self, PyObject *args) {
    Py_INCREF( Py_None );
    return Py_None;
}

static PyObject *bsgl_draw_test(PyObject *self, PyObject *args) {
    double width, height, offset_x, offset_y;
    double sz;
    double seconds; 

    if( !PyArg_ParseTuple( args, "dddddd", &width, &height, &seconds, &offset_x, &offset_y, &sz ) ) {
        return NULL;
    }

    const double period = 2.0;
    const double phase = fmod( seconds, 2.0 );
    double red;
    if( phase <= 1.0 ) {
        red = phase;
    } else {
        red = 2.0 - phase;
    }

    glLoadIdentity();                                   // Reset The Current Modelview Matrix
    glColor3f(red,0.5f,1.0f);                          // Set The Color To Blue One Time Only
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
    { "draw_test", bsgl_draw_test, METH_VARARGS, "Draw some test graphics." },
    { "initialize", bsgl_initialize, METH_VARARGS, "Initialize BSGL." },
    { NULL, NULL, 0, NULL }
};

PyMODINIT_FUNC initbsgl(void) {
    Py_InitModule( "bsgl", BsGLMethods );

    fprintf( stderr, "BSGL module initialized.\n" );
}
