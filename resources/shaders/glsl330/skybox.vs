#version 330

// Input vertex attributes
in vec3 vertexPosition;

// Input uniform values
uniform mat4 mvp;

// Output vertex attributes (to fragment shader)
out vec3 fragPosition;

void main()
{
    fragPosition = vertexPosition;

    // Calculate final vertex position, discarding translation to keep camera centered
    mat4 rotMatrix = mat4(mat3(mvp));
    vec4 clipPos = rotMatrix * vec4(vertexPosition, 1.0);

    // Force z to 1.0 so skybox is always drawn at maximum depth
    gl_Position = clipPos.xyww;
}
