#ifndef H_CGLUTIL
#define H_CGLUTIL

GLuint create_shader_from_file(GLenum type, const char *filename);
GLuint create_program(GLuint vertex_shader, GLuint fragment_shader );
GLuint create_static_buffer(GLenum target, const void *buffer_data, GLsizei buffer_size);
GLuint create_dynamic_buffer(GLenum target, const void *buffer_data, GLsizei buffer_size);

#endif
