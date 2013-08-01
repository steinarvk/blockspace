#version 110

uniform mat4 transformation;

attribute vec2 com_position;
attribute vec2 position_offset;
attribute vec2 attr_texcoord;
attribute vec4 tint;
attribute float angle;
attribute float internal_angle;

varying vec2 texcoord;
varying float v_rcosa, v_rsina;
varying vec4 v_tint;

void main() {
	if( tint.a <= 0.0 ) {
		gl_Position = vec4( -10.0, -10.0, -10.0, 1.0 );
	} else {
		float a = angle;
        float rcosa = cos(a);
		float rsina = sin(a);
        v_rcosa = cos(a + internal_angle);
        v_rsina = sin(a + internal_angle);
		vec2 rp = com_position + vec2(position_offset.x * rcosa - position_offset.y * rsina, position_offset.x * rsina + position_offset.y * rcosa );
//		gl_Position = vec4( rp.x / aspect, rp.y, 0.0, 1.0 );
        gl_Position = transformation * vec4(rp, 0.0, 1.0);
		texcoord = attr_texcoord;
		v_tint = tint;
	}
}
