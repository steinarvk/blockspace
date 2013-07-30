#ifndef H_BSGL_SYSTEM
#define H_BSGL_SYSTEM

#include <Python.h>
#include <GL/glew.h>

#include <stdbool.h>

#include "bsglarray.h"

typedef struct {
    PyObject_HEAD
    /* Type-specific fields go here. */

	GLushort *element_buffer_data;
	int element_buffer_data_size;

    struct bsgl_array vertex_buffer;

    bool element_buffer_dirty;
    bool vertex_buffer_dirty;

    int texture_id;

    int stride;

    GLfloat transformation_matrix[16];

    GLuint vertex_buffer_id, element_buffer_id;

    GLuint vertex_shader_id, fragment_shader_id, program_id;
    struct {
        GLint sheet_texture;
        GLint transformation;
    } uniforms;

    struct {
        GLint com_position;
        GLint position_offset;
        GLint attr_texcoord;
        GLint angle;
        GLint tint;
    } attributes;
} System;

extern PyTypeObject SystemType;

int bsgl_system_reallocate_elements( System *sys );

int bsgl_system_add( System *sys, int *out_index, double com_position[2], double offset[2], double angle, double sz[2], double tint[4], double texcoords[2], double texsize[2] );
int bsgl_system_remove( System *sys, int index );

int bsgl_system_upload_vertex_buffer( System *sys );
int bsgl_system_upload_element_buffer( System *sys );
int bsgl_system_refresh( System *sys );
int bsgl_system_draw( System *sys );
int bsgl_system_bind_vertex_attributes( System *sys );
int bsgl_system_unbind_vertex_attributes( System *sys );

int bsgl_system_setup_test_quads( System *sys, int n );

#endif
