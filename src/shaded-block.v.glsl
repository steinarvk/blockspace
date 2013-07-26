#version 110

uniform float fade_factor;

attribute vec2 position;
attribute vec2 attr_texcoord;

varying vec2 texcoord;
varying float rcosa, rsina;

void main() {
    float aspect = 640.0 / 480.0;
    float a = fade_factor;
    rcosa = cos(a);
    rsina = sin(a);
    vec2 rp = vec2(position.x * rcosa - position.y * rsina, position.x * rsina + position.y * rcosa );
    gl_Position = vec4( rp.x / aspect, rp.y, 0.0, 1.0 );
    texcoord = attr_texcoord;
}
