#version 110

uniform float fade_factor;
uniform sampler2D sheet_texture;

varying vec2 texcoord;

void main() {
    vec4 tint = vec4(0.7,0.2,0.2,0.9);
    gl_FragColor = texture2D( sheet_texture, texcoord ) * tint;
}

