#include <Python.h>
#include <structmember.h>

#include <GL/glew.h>

#include "bsglsystem.h"
#include "cglutil.h"

int bsgl_system_unbind_vertex_attributes( System *sys ) {
    const GLint attrs[] = {
        sys->attributes.com_position,
        sys->attributes.angle,
        sys->attributes.tint,
        sys->attributes.position_offset,
        sys->attributes.attr_texcoord
    };
    const int n = 5;

    for(int i = 0; i < n; i++) {
        glDisableVertexAttribArray( attrs[i] );
    }

    return 0;
}

int bsgl_system_bind_vertex_attributes( System *sys ) {
    const GLint attrs[] = {
        sys->attributes.com_position,
        sys->attributes.angle,
        sys->attributes.tint,
        sys->attributes.position_offset,
        sys->attributes.attr_texcoord
    };
    const int floats[] = {
        2,
        1,
        4,
        2,
        2
    };
    const int n = 5;

    int floatcount = 0;

    for(int i = 0; i < n; i++) {
        glVertexAttribPointer( attrs[i],
                               floats[i],
                               GL_FLOAT,
                               GL_FALSE,
                               sys->stride,
                               (void *) (floatcount * sizeof (GLfloat)) );
        floatcount += floats[i];
        glEnableVertexAttribArray( attrs[i] );
    }

    return 0;
};

int bsgl_system_remove( System *sys, int index ) {
    bsgl_array_remove( &sys->vertex_buffer, index );

    sys->vertex_buffer_dirty = true;

    return 0;
}

int bsgl_system_add( System *sys, int *out_index, double com_position[2], double offset[2], double angle, double sz[2], double tint[4], double texcoords[2], double texsize[2] ) {
    const int floats_per_vertex = 11;
    const double xs[] = { 0, 1, 0, 1 };
    const double ys[] = { 0, 0, 1, 1 };

    GLfloat data[floats_per_vertex*4];
    int float_count = 0;

    for(int i=0;i<4;i++) {
        assert( (float_count % floats_per_vertex) == 0 );

        data[float_count++] = com_position[0];
        data[float_count++] = com_position[1];
        data[float_count++] = angle;
        data[float_count++] = tint[0];
        data[float_count++] = tint[1];
        data[float_count++] = tint[2];
        data[float_count++] = tint[3];
        data[float_count++] = offset[0] + (xs[i]-0.5) * sz[0];
        data[float_count++] = offset[1] + (ys[i]-0.5) * sz[1];
        data[float_count++] = texcoords[0] + xs[i] * texsize[0];
        data[float_count++] = texcoords[1] + ys[i] * texsize[1];
    }

    const int datasize = float_count * sizeof data[0];

    assert( datasize == sys->vertex_buffer.element_size );

    int old_capacity = sys->vertex_buffer.capacity;

    int bsgl_index;
    if( bsgl_array_add_and_fill( &sys->vertex_buffer, &bsgl_index, data, datasize ) ) {
        return 1;
    }

    if( sys->vertex_buffer.capacity != old_capacity ) {
        if( bsgl_system_reallocate_elements( sys ) ) {
            return 1;
        }
    }

    int vertex_index = 4 * bsgl_index;
    int element_index = 6 * bsgl_index;
    const int element_quad_base[] = { 0, 1, 2, 3, 2, 1 };

    assert( vertex_index >= 0 );
    assert( vertex_index < 0xffff );

    for(int i = 0; i < 6; i++ ) {
        int element = vertex_index + element_quad_base[ i ];
        sys->element_buffer_data[ element_index++ ] = element;
    }

    sys->element_buffer_dirty = true;
    sys->vertex_buffer_dirty = true;

    if( out_index ) {
        *out_index = bsgl_index;
    }

    return 0;
}

int bsgl_system_reallocate_elements( System *sys ) {
    const int elements_per_quad = 6;
    const int number_of_elements = sys->vertex_buffer.capacity;
    const int required_size = number_of_elements * elements_per_quad * sizeof (GLushort);
    const int old_size = sys->element_buffer_data_size;

    assert( number_of_elements < 0xffff );
    assert( required_size > old_size );

    GLushort *new_data = realloc( sys->element_buffer_data, required_size );
    if( !new_data ) {
        return 1;
    }

    char * raw_data = (char*) new_data;

    memset( &raw_data[old_size], 0, required_size - old_size );
    sys->element_buffer_data_size = required_size;
    sys->element_buffer_data = new_data;

    sys->element_buffer_dirty = true;

    return 0;
}

int bsgl_system_upload_vertex_buffer( System *sys ) {
    glBindBuffer( GL_ARRAY_BUFFER, sys->vertex_buffer_id );
    glBufferData( GL_ARRAY_BUFFER, sys->vertex_buffer.array_byte_size, sys->vertex_buffer.data, GL_DYNAMIC_DRAW );

    sys->vertex_buffer_dirty = false;

    return 0;
}

int bsgl_system_upload_element_buffer( System *sys ) {
    glBindBuffer( GL_ELEMENT_ARRAY_BUFFER, sys->element_buffer_id );
    glBufferData( GL_ELEMENT_ARRAY_BUFFER, sys->element_buffer_data_size, sys->element_buffer_data, GL_DYNAMIC_DRAW );

    sys->element_buffer_dirty = false;

    return 0;
}

int bsgl_system_refresh( System *sys ) {
    if( sys->element_buffer_dirty ) {
        if( bsgl_system_upload_element_buffer( sys ) ) {
            return 1;
        }
    }

    if( sys->vertex_buffer_dirty ) {
        if( bsgl_system_upload_vertex_buffer( sys ) ) {
            return 1;
        }
    }

    return 0;
}

int bsgl_system_draw( System *sys ) {
    if( bsgl_system_refresh( sys ) ) {
        return 1;
    }

    glUseProgram( sys->program_id );

    glUniform1f( sys->uniforms.fade_factor, (GLfloat) 0.0 );
    glColor3f(1.f, 1.f, 1.f);
    glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
    glEnable( GL_BLEND );

    glActiveTexture( GL_TEXTURE0 );
    glBindTexture( GL_TEXTURE_2D, sys->texture_id );
    glUniform1i( sys->uniforms.sheet_texture, 0 );

    glBindBuffer( GL_ELEMENT_ARRAY_BUFFER, sys->element_buffer_id );

    glBindBuffer( GL_ARRAY_BUFFER, sys->vertex_buffer_id );

    if( bsgl_system_bind_vertex_attributes( sys ) ) {
        return 1;
    }

    int number_of_elements = 6 * sys->vertex_buffer.capacity;

    glDrawElements( GL_TRIANGLES, number_of_elements, GL_UNSIGNED_SHORT, (void*) 0 );

    if( bsgl_system_unbind_vertex_attributes( sys ) ) {
        return 1;
    }

    glUseProgram( 0 );

    return 0;
}

int bsgl_system_setup_test_quads(System *self, int number_of_things) {
    for(int k=0;k<number_of_things;k++) {
        double world_pos[] = { 0.0, 0.0 };
        double world_size[] = { 0.05, 0.05 };
        double offset[] = { 0.0, 0.0 };
        double texcoords[] = { 0.0, 0.0 };
        double texsize[] = { 1.0, 1.0 };
        double angle = (rand() / (double) RAND_MAX) * 6.28;
        double rgba[] = { 0.0, 0.0, 0.0, 1.0 };

        world_pos[0] = 2.7 * (rand() - RAND_MAX/2) / (double)RAND_MAX;
        world_pos[1] = 2.0 * (rand() - RAND_MAX/2) / (double)RAND_MAX;

        switch( rand() % 3 ) {
            case 0:
                rgba[0] = 0.5 + 0.5 * (rand() / (double) RAND_MAX);
                rgba[2] = 0.9 * (rand() / (double) RAND_MAX);
                rgba[1] = 0.0;
                break;
            case 1:
                rgba[2] = 0.5 + 0.5 * (rand() / (double) RAND_MAX);
                rgba[1] = 0.9 * (rand() / (double) RAND_MAX);
                rgba[0] = 0.0;
                break;
            case 2:
                rgba[1] = 0.5 + 0.5 * (rand() / (double) RAND_MAX);
                rgba[0] = 0.9 * (rand() / (double) RAND_MAX);
                rgba[2] = 0.0;
                break;
        }

        if( bsgl_system_add( self, NULL, world_pos, offset, angle, world_size, rgba, texcoords, texsize ) ) {
            return 1;
        }
    }

    return 0;
}

static int System_init(System *self, PyObject *args, PyObject *kwargs) {
    const int floats_per_vertex = 11;

    static char *kwlist[] = { "texture_id" };
    int arg_texture_id;
    if( !PyArg_ParseTupleAndKeywords( args, kwargs, "i", kwlist, &arg_texture_id ) ) {
        return -1;
    }


    do {
        self->texture_id = arg_texture_id;

        self->element_buffer_dirty = true;
        self->vertex_buffer_dirty = true;

        if( bsgl_array_initialize( &self->vertex_buffer, floats_per_vertex * 4 * sizeof (GLfloat)) ) {
            break;
        }

        self->vertex_buffer_id = create_dynamic_buffer(
            GL_ARRAY_BUFFER,
            NULL,
            0
        );

        self->element_buffer_id = create_dynamic_buffer(
            GL_ELEMENT_ARRAY_BUFFER,
            NULL,
            0
        );

        fprintf( stderr, "A\n" );
        self->vertex_shader_id = create_shader_from_file( GL_VERTEX_SHADER, "shaded-block.v.glsl" );
        if( !self->vertex_shader_id ) break;
        fprintf( stderr, "error: %d\n", glGetError() );

        fprintf( stderr, "B\n" );
        self->fragment_shader_id = create_shader_from_file( GL_FRAGMENT_SHADER, "shaded-block.f.glsl" );
        if( !self->fragment_shader_id ) break;

        fprintf( stderr, "error: %d\n", glGetError() );
        fprintf( stderr, "C\n" );
        self->program_id = create_program( self->vertex_shader_id, self->fragment_shader_id );
        if( !self->program_id ) break;

        fprintf( stderr, "error: %d\n", glGetError() );
        fprintf( stderr, "calling with program %d\n", self->program_id );

        self->uniforms.sheet_texture = glGetUniformLocation( self->program_id, "sheet_texture" );

        fprintf( stderr, "error: %d\n", glGetError() );

        self->uniforms.fade_factor = glGetUniformLocation( self->program_id, "fade_factor" );

        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.position_offset = glGetAttribLocation( self->program_id, "position_offset" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.com_position = glGetAttribLocation( self->program_id, "com_position" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.tint = glGetAttribLocation( self->program_id, "tint" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.angle = glGetAttribLocation( self->program_id, "angle" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->attributes.attr_texcoord = glGetAttribLocation( self->program_id, "attr_texcoord" );
        fprintf( stderr, "error: %d\n", glGetError() );

        self->stride = sizeof(GLfloat) * floats_per_vertex;

        fprintf( stderr, "Successfully created a System object!\n" );

        return 0;
    } while(0);

    fprintf( stderr, "Failed to initialize a System object\n" );
    return -1;
}

PyObject *System_draw(System *self, PyObject *args) {
    bsgl_system_draw( self );

    Py_INCREF( Py_None );
    return Py_None;
}

PyObject *System_reserve(System *self, PyObject *args) {
    int n = 0;

    if( !PyArg_ParseTuple( args, "i", &n ) ) {
        return NULL;
    }

    int old_capacity = self->vertex_buffer.capacity;

    if( bsgl_array_reserve( &self->vertex_buffer, n ) ) {
        return NULL;
    }

    if( self->vertex_buffer.capacity != old_capacity ) {
        if( bsgl_system_reallocate_elements( self ) ) {
            return NULL;
        }
    }

    Py_INCREF( Py_None );
    return Py_None;
}

PyObject *System_add(System *self, PyObject *args, PyObject *kwargs) {
    static char *kwlist[] = { "position", "offset", "angle", "size", "texture_coordinates", "texture_size", "colour" };

    double position[] = { 0.0, 0.0 };
    double offset[] = { 0.0, 0.0 };
    double angle = 0.0;
    double size[] = { 1.0, 1.0 };
    double texcoords[] = { 0.0, 0.0 };
    double texsize[] = { 1.0, 1.0 };
    double rgba[] = { 1.0, 1.0, 1.0, 1.0 };

    if( !PyArg_ParseTupleAndKeywords( args,
                                      kwargs,
                                      "|(dd)(dd)d(dd)(dd)(dd)(dddd)",
                                      kwlist, 
                                      &position[0], &position[1],
                                      &offset[0], &offset[1],
                                      &angle,
                                      &size[0], &size[1],
                                      &texcoords[0], &texcoords[1],
                                      &texsize[0], &texsize[1],
                                      &rgba[0], &rgba[1], &rgba[2], &rgba[3] ) ) {
        return NULL;
    }

    int index = -1;

    if( bsgl_system_add( self, &index, position, offset, angle, size, rgba, texcoords, texsize ) ) {
        return NULL;
    }

    return Py_BuildValue( "i", index );
}

PyObject *System_update_position_and_angle(System *self, PyObject *args) {
    int index = -1;
    double position[2];
    double angle;

    if( !PyArg_ParseTuple( args, "i(dd)d", &index, &position[0], &position[1], &angle ) ) {
        return NULL;
    }

    int vertex_index0 = 4 * index;
    const int floats_per_vertex = 11;
    GLfloat* floats = (void*) self->vertex_buffer.data;

    for(int i=0;i<4;i++) {
        int vindex = vertex_index0 + i;
        floats[ vindex * floats_per_vertex + 0 ] = position[0];
        floats[ vindex * floats_per_vertex + 1 ] = position[1];
        floats[ vindex * floats_per_vertex + 2 ] = angle;
    }

    self->vertex_buffer_dirty = true;

    Py_INCREF( Py_None );
    return Py_None;
}

PyObject *System_remove(System *self, PyObject *args) {
    int index = -1;
    if( !PyArg_ParseTuple( args, "i", &index ) ) {
        return NULL;
    }

    if( bsgl_system_remove( self, index ) ) {
        return NULL;
    }

    Py_INCREF( Py_None );
    return Py_None;
}

PyObject *System_get_capacity(System *self, PyObject *args) {
    return Py_BuildValue( "i", self->vertex_buffer.capacity );
}

PyObject *System_get_number_of_elements(System *self, PyObject *args) {
    return Py_BuildValue( "i", self->vertex_buffer.number_of_elements );
}

PyMemberDef System_members[] = {
//    { "first", T_OBJECTEX, offsetof(System, first), 0, "first name" },
    {NULL}
};

PyMethodDef System_methods[] = {
    { "draw", (PyCFunction) System_draw, METH_NOARGS, "Draw the system" },
    { "reserve", (PyCFunction) System_reserve, METH_VARARGS, "Pre-reserve space for system elements." },
    { "add", (PyCFunction) System_add, METH_VARARGS | METH_KEYWORDS, "Add an element to the system and return its index." },
    { "remove", (PyCFunction) System_remove, METH_VARARGS, "Remove an element by its index." },
    { "get_capacity", (PyCFunction) System_get_capacity, METH_NOARGS, "Get the number of elements for which space has been allocated." },
    { "get_number_of_elements", (PyCFunction) System_get_number_of_elements, METH_NOARGS, "Get the number of elements." },
    { "update_position_and_angle", (PyCFunction) System_update_position_and_angle, METH_VARARGS, "Update one element by setting its angle and center of mass position." },
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

