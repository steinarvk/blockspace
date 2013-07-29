#version 110

uniform float fade_factor;
uniform sampler2D sheet_texture;

varying vec2 texcoord;
varying float rcosa;
varying float rsina;
varying vec4 v_tint;

void main() {
    vec4 tint = v_tint;
    vec4 tex = texture2D( sheet_texture, texcoord );
    gl_FragColor = tex * tint;
}

