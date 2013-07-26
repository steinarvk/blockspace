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
    vec3 texvec = (tex.rgb - vec3(0.5)) * 2.0;
    float light_slope = 0.6123;
    vec2 light2d = vec2( -0.447213, 0.894427 ) * sqrt(1.0-light_slope*light_slope);
    vec3 light = vec3( light2d.x * rcosa - light2d.y * rsina, light2d.x * rsina + light2d.y * rcosa, light_slope );
    float shade = (dot( texvec, light ) + 1.0) * 0.5;
    float dark = 0.2;
    float shade_scaled = dark + shade * (1.0-dark);
    gl_FragColor = vec4( vec3(shade_scaled), tex.a ) * tint;
}

