#version 330

in vec2 fragTexCoord;
in vec4 fragColor;

#define MAX_LENSES 8

uniform sampler2D texture0;
uniform vec2 lensScreenPos[MAX_LENSES];
uniform float lensRadius[MAX_LENSES];
uniform int isBehindCamera[MAX_LENSES];
uniform int lensCount;         // how many of the MAX_LENSES entries above are actually active this frame
uniform float lensingStrength; // shared by all lenses
uniform float aspectRatio;

out vec4 finalColor;

void main()
{
    vec2 aspectCorrection = vec2(aspectRatio, 1.0);
    vec2 totalOffset = vec2(0.0);
    bool insideSingularity = false;

    for (int i = 0; i < lensCount; i++)
    {
        if (isBehindCamera[i] == 1 ||
            lensScreenPos[i].x < -0.5 || lensScreenPos[i].x > 1.5 ||
            lensScreenPos[i].y < -0.5 || lensScreenPos[i].y > 1.5)
        {
            continue; // this particular black hole is off-screen/behind camera - skip it
        }

        vec2 delta = (fragTexCoord - lensScreenPos[i]) * aspectCorrection;
        float dist = length(delta);

        if (dist < lensRadius[i])
        {
            // Inside this singularity's solid core - nothing else matters, it's black
            insideSingularity = true;
            break;
        }

        // Accumulate this lens's contribution to the total distortion
        float factor = lensingStrength / (dist - lensRadius[i] + 0.005);
        totalOffset += normalize(delta) * factor / aspectCorrection;
    }

    if (insideSingularity)
    {
        finalColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    vec2 distortedCoord = clamp(fragTexCoord - totalOffset, vec2(0.001), vec2(0.999));
    finalColor = texture(texture0, distortedCoord) * fragColor;
}
