#ifndef H_BSGL_SYSTEM
#define H_BSGL_SYSTEM

#include <Python.h>
#include <GL/glew.h>

typedef struct {
    PyObject_HEAD
    /* Type-specific fields go here. */

    GLuint vertex_buffer, element_buffer;

    GLuint vertex_shader, fragment_shader, program;
    struct {
        GLint fade_factor;
    } uniforms;

    struct {
        GLint position;
    } attributes;

    GLfloat fade_factor;
} System;

extern PyTypeObject SystemType;

#endif
