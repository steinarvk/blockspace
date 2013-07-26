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

    GLuint vertex_buffer, element_buffer;

    GLuint vertex_shader, fragment_shader, program;
    struct {
        GLint fade_factor;
        GLuint sheet_texture;
    } uniforms;

    struct {
        GLint position;
        GLint attr_texcoord;
    } attributes;

    GLfloat fade_factor;
} System;

extern PyTypeObject SystemType;

#endif
