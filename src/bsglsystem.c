#include <Python.h>
#include <structmember.h>

#include <GL/glew.h>

#include "bsglsystem.h"
#include "cglutil.h"

static int System_init(System *self, PyObject *args, PyObject *kwargs) {
    int floats_per_vertex = 4;
    GLfloat vertex_buffer_data[ 4 * floats_per_vertex ];
    const int base_s[2][4] = { {0, 1, 0, 1}, {0, 0, 1, 1} };
    static const GLushort element_buffer_data[] = { 0, 1, 2, 3 };

    static char *kwlist[] = { "texture_id", "texture_coordinates", "texture_size" };
    int arg_texture_id;
    float texture_coordinates[2];
    float texture_size[2];
    PyObject * arg_texture_coordinates = NULL, *arg_texture_size = NULL;
    if( !PyArg_ParseTupleAndKeywords( args, kwargs, "iOO", kwlist, &arg_texture_id, &arg_texture_coordinates, &arg_texture_size ) ) {
        return -1;
    }
    if( !PyArg_ParseTuple( arg_texture_coordinates, "ff", &texture_coordinates[0], &texture_coordinates[1] ) ) {
        return -1;
    }
    if( !PyArg_ParseTuple( arg_texture_size, "ff", &texture_size[0], &texture_size[1] ) ) {
        return -1;
    }

    fprintf( stderr, "%f %f\n", texture_size[0], texture_size[1] );

    double world_pos[] = { -1, -1 };
    double world_size[] = { 2, 2 };

    int index = 0;

    for(int i=0;i<4;i++) {
        for(int j=0;j<2;j++) {
            vertex_buffer_data[index++] = world_pos[j] + base_s[j][i] * world_size[j];
        }
        for(int j=0;j<2;j++) {
            vertex_buffer_data[index++] = texture_coordinates[j] + base_s[j][i] * texture_size[j];
        }
    }

    for(int i=0;i<16;i++) {
        fprintf(stderr, "%f\n",  vertex_buffer_data[i] );
    }

    do {
        self->texture_id = arg_texture_id;

        for(int i=0;i<2;i++) {
            self->texture_coordinates[i] = texture_coordinates[i];
            self->texture_size[i] = texture_size[i];
        }

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

        self->uniforms.sheet_texture = glGetUniformLocation( self->program, "sheet_texture" );

        fprintf( stderr, "error: %d\n", glGetError() );

        self->uniforms.fade_factor = glGetUniformLocation( self->program, "fade_factor" );

        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.position = glGetAttribLocation( self->program, "position" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.attr_texcoord = glGetAttribLocation( self->program, "attr_texcoord" );
        fprintf( stderr, "error: %d\n", glGetError() );

        fprintf( stderr, "Successfully created a System object!\n" );

        return 0;
    } while(0);

    fprintf( stderr, "Failed to initialize a System object\n" );
    return -1;
}

static PyObject *System_draw(System *self, PyObject *args) {
    double offset_x = 300, offset_y = 200;
    double sz = 100;
    double seconds; 

    if( !PyArg_ParseTuple( args, "d", &seconds ) ) {
        return NULL;
    }

    glUseProgram( self->program );
    glUniform1f( self->uniforms.fade_factor, (GLfloat) seconds );
    glColor3f(1.f,1.f,1.f);

    glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
    glEnable( GL_BLEND );

    glBindTexture( GL_TEXTURE_2D, self->texture_id );
    glUniform1i( self->uniforms.sheet_texture, 0 );

    glBindBuffer( GL_ARRAY_BUFFER, self->vertex_buffer );
    glVertexAttribPointer(
        self->attributes.position,
        2,
        GL_FLOAT,
        GL_FALSE,
        sizeof(GLfloat) * 4,
        (void*) 0
    );
    glEnableVertexAttribArray( self->attributes.position );
    glVertexAttribPointer(
        self->attributes.attr_texcoord,
        2,
        GL_FLOAT,
        GL_FALSE,
        sizeof(GLfloat) * 4,
        (void*) ( sizeof(GLfloat) * 2 )
    );
    glEnableVertexAttribArray( self->attributes.attr_texcoord );

    glBindBuffer( GL_ELEMENT_ARRAY_BUFFER, self->element_buffer );
    glDrawElements( GL_TRIANGLE_STRIP, 4, GL_UNSIGNED_SHORT, (void*) 0 );

    glDisableVertexAttribArray( self->attributes.position );
    glDisableVertexAttribArray( self->attributes.attr_texcoord );

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

