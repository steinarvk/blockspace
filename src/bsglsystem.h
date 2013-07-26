#ifndef H_BSGL_SYSTEM
#define H_BSGL_SYSTEM

#include <Python.h>
#include <GL/glew.h>

typedef struct {
    PyObject_HEAD
    /* Type-specific fields go here. */

    int texture_id;
    float texture_coordinates[2];
    float texture_size[2];

    int stride;

    int number_of_elements;

    GLuint vertex_buffer, element_buffer;

    GLuint vertex_shader, fragment_shader, program;
    struct {
        GLint fade_factor;
        GLuint sheet_texture;
    } uniforms;

    struct {
        GLint com_position;
        GLint position_offset;
        GLint attr_texcoord;
        GLint angle;
    } attributes;

    GLfloat fade_factor;
} System;

extern PyTypeObject SystemType;

#endif
