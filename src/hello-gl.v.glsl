#version 110

uniform float fade_factor;

attribute vec2 position;
attribute vec2 attr_texcoord;

varying vec2 texcoord;

void main() {
    float aspect = 640.0 / 480.0;
    float a = fade_factor;
    vec2 rp = vec2(position.x * cos( a ) - position.y * sin( a ), position.x * sin(a) + position.y * cos(a) );
    gl_Position = vec4( rp.x / aspect, rp.y, 0.0, 1.0 );
    texcoord = attr_texcoord;
}
