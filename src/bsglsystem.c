#include <Python.h>
#include <structmember.h>

#include <GL/glew.h>

#include "bsglsystem.h"
#include "cglutil.h"

static int System_init(System *self, PyObject *args, PyObject *kwargs) {
    const int number_of_things = 5000;
    const int floats_per_vertex = 11;
    const int number_of_elements = number_of_things * 6;
    GLfloat vertex_buffer_data[ 4 * floats_per_vertex * number_of_things ];
    const int base_s[2][4] = { {0, 1, 0, 1}, {0, 0, 1, 1} };
    static const GLushort element_buffer_data_base[] = { 0, 1, 2, 3, 2, 1 };
    GLushort element_buffer_data[number_of_elements];

    for(int i=0;i<number_of_elements;i++) {
        element_buffer_data[i] = 4 * (i/6) + element_buffer_data_base[i%6];
    }

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

    double world_pos[] = { 0.0, 0.0 };
    double world_size[] = { 0.4, 0.4 };

    int index = 0;

    for(int k=0;k<number_of_things;k++) {
        world_pos[0] = 2.7 * (rand() - RAND_MAX/2) / (double)RAND_MAX;
        world_pos[1] = 2.0 * (rand() - RAND_MAX/2) / (double)RAND_MAX;
        double angle = (rand() / (double) RAND_MAX) * 6.28;
        double red = 0.0;
        double blue = 0.0;
        double green = 0.0;
        double alpha = 1.0;

		if( rand() % 100 ) {
			alpha = 0.0;
		}

        switch( rand() % 3 ) {
            case 0:
                red = 0.5 + 0.5 * (rand() / (double) RAND_MAX);
                green = 0.9 * (rand() / (double) RAND_MAX);
                blue = 0.0;
                break;
            case 1:
                green = 0.5 + 0.5 * (rand() / (double) RAND_MAX);
                blue = 0.9 * (rand() / (double) RAND_MAX);
                red = 0.0;
                break;
            case 2:
                blue = 0.5 + 0.5 * (rand() / (double) RAND_MAX);
                red = 0.9 * (rand() / (double) RAND_MAX);
                green = 0.0;
                break;
        }

        for(int i=0;i<4;i++) {
            for(int j=0;j<2;j++) {
//                vertex_buffer_data[index++] = world_pos[j];
                vertex_buffer_data[index++] = 0;
            }
            for(int j=0;j<2;j++) {
//                vertex_buffer_data[index++] = (base_s[j][i]-0.5) * 0.5 * world_size[j];
                vertex_buffer_data[index++] = world_pos[j] + 0.5 * world_size[j] + (base_s[j][i]-0.5) * 0.5 * world_size[j];
            }
            for(int j=0;j<2;j++) {
                vertex_buffer_data[index++] = texture_coordinates[j] + base_s[j][i] * texture_size[j];
            }

            vertex_buffer_data[index++] = red;
            vertex_buffer_data[index++] = green;
            vertex_buffer_data[index++] = blue;
            vertex_buffer_data[index++] = alpha;

            vertex_buffer_data[index++] = angle;
        }
    }

    do {
        self->texture_id = arg_texture_id;

        self->number_of_elements = number_of_elements;

        for(int i=0;i<2;i++) {
            self->texture_coordinates[i] = texture_coordinates[i];
            self->texture_size[i] = texture_size[i];
        }

        self->vertex_buffer = create_stream_buffer(
            GL_ARRAY_BUFFER,
            vertex_buffer_data,
            sizeof(vertex_buffer_data)
        );

        self->element_buffer = create_dynamic_buffer(
            GL_ELEMENT_ARRAY_BUFFER,
            element_buffer_data,
            sizeof(element_buffer_data)
        );

		// memory leak! TODO
		self->vertex_buffer_data = malloc( sizeof (vertex_buffer_data) );
		self->vertex_buffer_data_size = sizeof vertex_buffer_data;
		memcpy( self->vertex_buffer_data, vertex_buffer_data, sizeof vertex_buffer_data );
		self->element_buffer_data = malloc( sizeof (element_buffer_data) );
		memcpy( self->element_buffer_data, element_buffer_data, sizeof element_buffer_data );
		self->element_buffer_data_size = sizeof element_buffer_data;
		// end known memory leak TODO

        fprintf( stderr, "A\n" );
        self->vertex_shader = create_shader_from_file( GL_VERTEX_SHADER, "shaded-block.v.glsl" );
        if( !self->vertex_shader ) break;
        fprintf( stderr, "error: %d\n", glGetError() );

        fprintf( stderr, "B\n" );
        self->fragment_shader = create_shader_from_file( GL_FRAGMENT_SHADER, "shaded-block.f.glsl" );
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

        self->attributes.position_offset = glGetAttribLocation( self->program, "position_offset" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.com_position = glGetAttribLocation( self->program, "com_position" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.tint = glGetAttribLocation( self->program, "tint" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.angle = glGetAttribLocation( self->program, "angle" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.attr_texcoord = glGetAttribLocation( self->program, "attr_texcoord" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->stride = sizeof(GLfloat) * 11;

        fprintf( stderr, "Successfully created a System object!\n" );

        return 0;
    } while(0);

    fprintf( stderr, "Failed to initialize a System object\n" );
    return -1;
}

static PyObject *System_draw(System *self, PyObject *args) {
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
	glBufferData( GL_ARRAY_BUFFER, self->vertex_buffer_data_size, self->vertex_buffer_data, GL_STREAM_DRAW );

    glVertexAttribPointer(
        self->attributes.com_position,
        2,
        GL_FLOAT,
        GL_FALSE,
        self->stride,
        (void*) 0
    );
    glEnableVertexAttribArray( self->attributes.com_position );
    glVertexAttribPointer(
        self->attributes.position_offset,
        2,
        GL_FLOAT,
        GL_FALSE,
        self->stride,
        (void*) ( sizeof(GLfloat) * 2 )
    );
    glEnableVertexAttribArray( self->attributes.position_offset );
    glVertexAttribPointer(
        self->attributes.attr_texcoord,
        2,
        GL_FLOAT,
        GL_FALSE,
        self->stride,
        (void*) ( sizeof(GLfloat) * 4 )
    );
    glEnableVertexAttribArray( self->attributes.attr_texcoord );
    glVertexAttribPointer(
        self->attributes.tint,
        4,
        GL_FLOAT,
        GL_FALSE,
        self->stride,
        (void*) ( sizeof(GLfloat) * 6 )
    );
    glEnableVertexAttribArray( self->attributes.tint );
    glVertexAttribPointer(
        self->attributes.angle,
        1,
        GL_FLOAT,
        GL_FALSE,
        self->stride,
        (void*) ( sizeof(GLfloat) * 10 )
    );
    glEnableVertexAttribArray( self->attributes.angle );

    glBindBuffer( GL_ELEMENT_ARRAY_BUFFER, self->element_buffer );
	glBufferData( GL_ELEMENT_ARRAY_BUFFER, self->element_buffer_data_size, self->element_buffer_data, GL_STREAM_DRAW );
    glDrawElements( GL_TRIANGLES, self->number_of_elements, GL_UNSIGNED_SHORT, (void*) 0 );

    glDisableVertexAttribArray( self->attributes.com_position );
    glDisableVertexAttribArray( self->attributes.position_offset );
    glDisableVertexAttribArray( self->attributes.attr_texcoord );
    glDisableVertexAttribArray( self->attributes.angle );
    glDisableVertexAttribArray( self->attributes.tint );

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

