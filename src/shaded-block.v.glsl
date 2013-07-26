#version 110

uniform float fade_factor;

attribute vec2 com_position;
attribute vec2 position_offset;
attribute vec2 attr_texcoord;
attribute float angle;

varying vec2 texcoord;
varying float rcosa, rsina;

void main() {
    float aspect = 640.0 / 480.0;
    float a = angle + fade_factor;
    rcosa = cos(a);
    rsina = sin(a);
    vec2 rp = com_position + vec2(fade_factor*0.05,fade_factor*0.1) + vec2(position_offset.x * rcosa - position_offset.y * rsina, position_offset.x * rsina + position_offset.y * rcosa );
    gl_Position = vec4( rp.x / aspect, rp.y, 0.0, 1.0 );
    texcoord = attr_texcoord;
}
