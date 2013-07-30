#version 110

uniform mat4 transformation;

attribute vec2 com_position;
attribute vec2 position_offset;
attribute vec2 attr_texcoord;
attribute vec4 tint;
attribute float angle;

varying vec2 texcoord;
varying float rcosa, rsina;
varying vec4 v_tint;

void main() {
	if( tint.a <= 0.0 ) {
		gl_Position = vec4( -10.0, -10.0, -10.0, 1.0 );
	} else {
		float a = angle;
		rcosa = cos(a);
		rsina = sin(a);
		vec2 rp = com_position + vec2(position_offset.x * rcosa - position_offset.y * rsina, position_offset.x * rsina + position_offset.y * rcosa );
//		gl_Position = vec4( rp.x / aspect, rp.y, 0.0, 1.0 );
        gl_Position = transformation * vec4(rp, 0.0, 1.0);
		texcoord = attr_texcoord;
		v_tint = tint;
	}
}
