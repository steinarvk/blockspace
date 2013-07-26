#version 110

uniform float fade_factor;

varying vec2 texcoord;

void main() {
    vec4 color_one = vec4(texcoord.x, texcoord.y, 0.5, 1.0);
    vec4 color_two = vec4(0.5, texcoord.x, texcoord.y, 1.0);
    gl_FragColor = mix( color_one, color_two, fade_factor );
}

