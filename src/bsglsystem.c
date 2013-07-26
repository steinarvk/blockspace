#include <Python.h>
#include <structmember.h>

#include <GL/glew.h>

#include "bsglsystem.h"
#include "cglutil.h"

static int System_init(System *self, PyObject *args, PyObject *kwargs) {
    static const GLfloat vertex_buffer_data[] = { 
        0.0f, -1.0f,
        1.0f, -1.0f,
        0.0f,  1.0f,
         1.0f,  1.0f
    };
    static const GLushort element_buffer_data[] = { 0, 1, 2, 3 };


    do {
        self->vertex_buffer = create_buffer(
            GL_ARRAY_BUFFER,
            vertex_buffer_data,
            sizeof(vertex_buffer_data)
        );
        self->element_buffer = create_buffer(
            GL_ELEMENT_ARRAY_BUFFER,
            element_buffer_data,
            sizeof(element_buffer_data)
        );

        fprintf( stderr, "A\n" );
        self->vertex_shader = create_shader_from_file( GL_VERTEX_SHADER, "hello-gl.v.glsl" );
        if( !self->vertex_shader ) break;
        fprintf( stderr, "error: %d\n", glGetError() );

        fprintf( stderr, "B\n" );
        self->fragment_shader = create_shader_from_file( GL_FRAGMENT_SHADER, "hello-gl.f.glsl" );
        if( !self->fragment_shader ) break;

        fprintf( stderr, "error: %d\n", glGetError() );
        fprintf( stderr, "C\n" );
        self->program = create_program( self->vertex_shader, self->fragment_shader );
        if( !self->program ) break;

        fprintf( stderr, "error: %d\n", glGetError() );
        fprintf( stderr, "calling with program %d\n", self->program );

        self->uniforms.fade_factor = glGetUniformLocation( self->program, "fade_factor" );

        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.position = glGetAttribLocation( self->program, "position" );

        fprintf( stderr, "error: %d\n", glGetError() );

        fprintf( stderr, "Successfully created a System object!\n" );

        return 0;
    } while(0);

    fprintf( stderr, "Failed to initialize a System object\n" );
    return -1;
}

static PyObject *System_draw(System *self, PyObject *args) {
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

    glUseProgram( self->program );
    glUniform1f( self->uniforms.fade_factor, (GLfloat) red );
    glColor3f(1.f,1.f,1.f);
    glLoadIdentity();                                   // Reset The Current Modelview Matrix
    glBindBuffer( GL_ARRAY_BUFFER, self->vertex_buffer );
    glVertexAttribPointer(
        self->attributes.position,
        2,
        GL_FLOAT,
        GL_FALSE,
        sizeof(GLfloat) * 2,
        (void*) 0
    );
    glEnableVertexAttribArray( self->attributes.position );

    glBindBuffer( GL_ELEMENT_ARRAY_BUFFER, self->element_buffer );
    glDrawElements( GL_TRIANGLE_STRIP, 4, GL_UNSIGNED_SHORT, (void*) 0 );

    glDisableVertexAttribArray( self->attributes.position );

    glUseProgram( 0 ); // Without this Pyglet will stop working

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

