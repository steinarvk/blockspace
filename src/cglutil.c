#include <GL/glew.h>

#include <stdio.h>
#include <stdlib.h>

#include "cglutil.h"

/* Based on code from Joe Groff's tutorial https://github.com/jckarter/hello-gl */

static void *read_file_contents(const char *filename, GLint *length)
{
    FILE *f = fopen(filename, "r");
    void *buffer;

    if (!f) {
        fprintf(stderr, "Unable to open %s for reading\n", filename);
        return NULL;
    }

    fseek(f, 0, SEEK_END);
    *length = ftell(f);
    fseek(f, 0, SEEK_SET);

    buffer = malloc(*length+1);
    *length = fread(buffer, 1, *length, f);
    fclose(f);
    ((char*)buffer)[*length] = '\0';

    return buffer;
}

static void show_gl_info_log(
    GLuint object,
    PFNGLGETSHADERIVPROC glGet__iv,
    PFNGLGETSHADERINFOLOGPROC glGet__InfoLog
)
{
    GLint log_length;
    char *log;

    glGet__iv(object, GL_INFO_LOG_LENGTH, &log_length);
    log = malloc(log_length);
    glGet__InfoLog(object, log_length, NULL, log);
    fprintf(stderr, "%s", log);
    free(log);
}


GLuint create_shader_from_file(GLenum type, const char *filename) {
    int length;
    GLchar *source = read_file_contents( filename, &length );
    GLuint shader;
    GLint shader_ok;

    shader = glCreateShader( type );

    glShaderSource( shader, 1, (const GLchar**) &source, &length );

    free( source );

    glCompileShader( shader );

    glGetShaderiv( shader, GL_COMPILE_STATUS, &shader_ok );
    if( !shader_ok ) {
        fprintf( stderr, "Failed to compile %s:\n", filename );
        show_gl_info_log( shader, glGetShaderiv, glGetShaderInfoLog );
        glDeleteShader( shader );
        return 0;
    }

    fprintf( stderr, "created shader %d\n", shader );

    return shader;
}

GLuint create_program(GLuint vertex_shader, GLuint fragment_shader ) {
    GLint program_ok;

    GLuint program = glCreateProgram();
    glAttachShader( program, vertex_shader );
    glAttachShader( program, fragment_shader );
    glLinkProgram( program );

    glGetProgramiv( program, GL_LINK_STATUS, &program_ok );
    if( !program_ok ) {
        fprintf( stderr, "Failed to link shader program:\n" );
        show_gl_info_log( program, glGetProgramiv, glGetProgramInfoLog );
        glDeleteProgram( program );
        return 0;
    }

    fprintf( stderr, "created program %d\n", program );

    return program;
}

GLuint create_static_buffer(
    GLenum target,
    const void *buffer_data,
    GLsizei buffer_size
) {
    GLuint buffer;
    glGenBuffers(1, &buffer);
    glBindBuffer(target, buffer);
    glBufferData(target, buffer_size, buffer_data, GL_STATIC_DRAW);
    return buffer;
}

GLuint create_dynamic_buffer(
    GLenum target,
    const void *buffer_data,
    GLsizei buffer_size
) {
    GLuint buffer;
    glGenBuffers(1, &buffer);
    glBindBuffer(target, buffer);
    glBufferData(target, buffer_size, buffer_data, GL_DYNAMIC_DRAW);
    return buffer;
}

