#version 330

// Input vertex attributes (from vertex shader)
in vec3 fragPosition;

// Input uniform values
uniform samplerCube environmentMap;
uniform bool doGamma;
uniform bool vflipped;

// Output fragment color
out vec4 finalColor;

void main()
{
    vec3 ray = fragPosition;
    if (vflipped) ray.y = -ray.y;

    // Sample the cubemap texture
    vec4 color = texture(environmentMap, ray);

    // Optional gamma correction
    if (doGamma)
    {
        color.rgb = pow(color.rgb, vec3(1.0/2.2));
    }

    finalColor = color;
}
