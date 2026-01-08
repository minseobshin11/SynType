#pragma once

#define MAX_VOICES 32

struct Voice {
    bool active;
    float frequency;
    float velocity; // 0.0 - 1.0
    float phase;    // Current phase state
    float noteTime; // Time in seconds since note triggered
    bool release;   // Is in release phase?
    float releaseTime; // Time when release started
    int note;       // MIDI note number
};

struct SynthState {
    Voice voices[MAX_VOICES];
    float masterVolume;
    int waveform; // 0=Sine, 1=Saw, 2=Square, 3=Triangle, 4=Noise
};
