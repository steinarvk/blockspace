#include <Python.h>
#include <structmember.h>

#include <GL/gl.h>

#include "bsglsystem.h"

static PyObject *System_draw(PyObject *self, PyObject *args) {
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

PyMemberDef System_members[] = {
//    { "first", T_OBJECTEX, offsetof(System, first), 0, "first name" },
    {NULL}
};

PyMethodDef System_methods[] = {
    { "draw", (PyCFunction) System_draw, METH_VARARGS, "Draw the system" },
    { NULL }
};

static void System_dealloc(System *self) {
    fprintf( stderr, "Deallocating a System object\n" );
    // Py_XDECREF members
    self->ob_type->tp_free( (PyObject*) self );
}

static int System_init(System *self, PyObject *args, PyObject *kwargs) {
    fprintf( stderr, "Initialized a System object\n" );
    return 0;
}

PyTypeObject SystemType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "bsgl.System",             /*tp_name*/
    sizeof(System),            /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor) System_dealloc,            /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,        /*tp_flags*/
    "BSGL System object",           /* tp_doc */
    0,                     /* tp_traverse */
    0,                     /* tp_clear */
    0,                     /* tp_richcompare */
    0,                     /* tp_weaklistoffset */
    0,                     /* tp_iter */
    0,                     /* tp_iternext */
    System_methods,             /* tp_methods */
    System_members,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)System_init,      /* tp_init */
    0,                         /* tp_alloc */
    PyType_GenericNew,                 /* tp_new */
};

