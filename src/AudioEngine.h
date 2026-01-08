#include <portaudio.h>
#include <vector>
#include "SharedState.h"
#include "MidiEngine.h"

class AudioEngine {
public:
    AudioEngine();
    ~AudioEngine();

    bool init();
    bool start();
    bool stop();
    bool cleanup();
    
    void setMidiEngine(MidiEngine* midi);
    void setWaveform(int type);

private:
    void handleMidi();
    void handleNoteOn(const MidiMessage& msg);
    void handleNoteOff(const MidiMessage& msg);
    
    static int paCallback(const void *inputBuffer, void *outputBuffer,
                          unsigned long framesPerBuffer,
                          const PaStreamCallbackTimeInfo* timeInfo,
                          PaStreamCallbackFlags statusFlags,
                          void *userData);

    int processAudio(const float* input, float* output, unsigned long frames);

    PaStream* stream;
    bool initialized;
    unsigned int sampleRate;
    unsigned int bufferSize;
    MidiEngine* midiEngine;
    SynthState hostState;
};
