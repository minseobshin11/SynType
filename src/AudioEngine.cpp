#include "AudioEngine.h"
#include "kernels.h"
#include <iostream>
#include <cstring>
#include <math.h>

AudioEngine::AudioEngine() : stream(nullptr), initialized(false), sampleRate(44100), bufferSize(512), midiEngine(nullptr) {
    // Initialize voices
    for (int i = 0; i < MAX_VOICES; ++i) {
        hostState.voices[i].active = false;
        hostState.voices[i].phase = 0.0f;
        hostState.voices[i].velocity = 0.0f;
    }
    hostState.masterVolume = 0.5f;
}

AudioEngine::~AudioEngine() {
    cleanup();
}

bool AudioEngine::init() {
    PaError err = Pa_Initialize();
    if (err != paNoError) {
        std::cerr << "PortAudio error: " << Pa_GetErrorText(err) << std::endl;
        return false;
    }
    
    // Initialize CUDA resources
    if (!initCUDA(bufferSize)) {
         std::cerr << "CUDA Initialization failed." << std::endl;
         return false;
    }

    initialized = true;
    return true;
}

bool AudioEngine::start() {
    if (!initialized) return false;

    PaError err = Pa_OpenDefaultStream(&stream,
                                       0,          // no input channels for now
                                       2,          // stereo output
                                       paFloat32,  // 32 bit floating point output
                                       sampleRate,
                                       bufferSize,
                                       &AudioEngine::paCallback,
                                       this);

    if (err != paNoError) {
        std::cerr << "PortAudio OpenStream error: " << Pa_GetErrorText(err) << std::endl;
        return false;
    }

    err = Pa_StartStream(stream);
    if (err != paNoError) {
        std::cerr << "PortAudio StartStream error: " << Pa_GetErrorText(err) << std::endl;
        return false;
    }

    return true;
}

void AudioEngine::setMidiEngine(MidiEngine* midi) {
    midiEngine = midi;
}

void AudioEngine::setWaveform(int type) {
    hostState.waveform = type;
}

void AudioEngine::handleMidi() {
    if (!midiEngine) return;
    
    std::vector<MidiMessage> msgs = midiEngine->getPendingMessages();
    for (const auto& msg : msgs) {
        if (msg.bytes.size() < 3) continue;
        
        unsigned char status = msg.bytes[0] & 0xF0;
        unsigned char velocity = msg.bytes[2];
        
        if (status == 0x90 && velocity > 0) { // Note On
            handleNoteOn(msg);
        } else if (status == 0x80 || (status == 0x90 && velocity == 0)) { // Note Off
            handleNoteOff(msg);
        }
    }
}

bool AudioEngine::stop() {
    if (stream) {
        Pa_StopStream(stream);
        Pa_CloseStream(stream);
        stream = nullptr;
    }
    return true;
}

bool AudioEngine::cleanup() {
    stop();
    Pa_Terminate();
    cleanupCUDA();
    initialized = false;
    return true;
}

int AudioEngine::paCallback(const void *inputBuffer, void *outputBuffer,
                            unsigned long framesPerBuffer,
                            const PaStreamCallbackTimeInfo* timeInfo,
                            PaStreamCallbackFlags statusFlags,
                            void *userData) {
    (void)timeInfo;
    (void)statusFlags;
    AudioEngine* engine = (AudioEngine*)userData;
    float* out = (float*)outputBuffer;
    
    // Silence output by default
    // memset(out, 0, framesPerBuffer * 2 * sizeof(float));
    
    // Call member function to process
    return engine->processAudio((const float*)inputBuffer, out, framesPerBuffer);
}

// Helper to find free voice
void AudioEngine::handleNoteOn(const MidiMessage& msg) {
    int note = msg.bytes.at(1);
    float velocity = msg.bytes.at(2) / 127.0f;
    
    // Check if note is already playing (retrigger)
    for (int i = 0; i < MAX_VOICES; ++i) {
        if (hostState.voices[i].active && hostState.voices[i].note == note && !hostState.voices[i].release) {
            hostState.voices[i].noteTime = 0.0f; // Reset env
            hostState.voices[i].velocity = velocity;
            return;
        }
    }

    // Find free voice
    for (int i = 0; i < MAX_VOICES; ++i) {
        if (!hostState.voices[i].active) {
            hostState.voices[i].active = true;
            hostState.voices[i].note = note;
            hostState.voices[i].velocity = velocity;
            hostState.voices[i].frequency = 440.0f * powf(2.0f, (note - 69.0f) / 12.0f);
            hostState.voices[i].phase = 0.0f; 
            hostState.voices[i].noteTime = 0.0f;
            hostState.voices[i].release = false;
            hostState.voices[i].releaseTime = 0.0f;
            return;
        }
    }
}

void AudioEngine::handleNoteOff(const MidiMessage& msg) {
    int note = msg.bytes.at(1);
    for (int i = 0; i < MAX_VOICES; ++i) {
        if (hostState.voices[i].active && hostState.voices[i].note == note) {
            if (!hostState.voices[i].release) {
                 hostState.voices[i].release = true;
                 hostState.voices[i].releaseTime = hostState.voices[i].noteTime;
            }
        }
    }
}


int AudioEngine::processAudio(const float* input, float* output, unsigned long frames) {
    (void)input;
    // 1. Handle MIDI events
    handleMidi();

    // 2. Transfer State to GPU
    updateStateCUDA(hostState);
    
    // 3. Process DSP on GPU
    processAudioCUDA(output, frames, 0.0f); // Time arg unused?
    
    // 4. Update Host State for NEXT buffer (Phase & Time)
    float dt = (float)frames / (float)sampleRate;
    for (int i = 0; i < MAX_VOICES; ++i) {
        if (hostState.voices[i].active) {
            // Update Phase
            float phaseInc = hostState.voices[i].frequency * 2.0f * M_PI * dt;
            hostState.voices[i].phase = fmodf(hostState.voices[i].phase + phaseInc, 2.0f * M_PI);
            
            // Update Note Timer
            hostState.voices[i].noteTime += dt;
            
            // Handle Lifecycle (Deactivation)
            if (hostState.voices[i].release) {
                float timeSinceRelease = hostState.voices[i].noteTime - hostState.voices[i].releaseTime;
                
                // Must match GPU release envelope times!
                // Massive = 1.0s, Others = 0.05s
                float releaseDuration = (hostState.waveform == 5) ? 1.0f : 0.05f;
                
                // Add a small buffer to ensure GPU fully renders the tail silence/fade
                if (timeSinceRelease > (releaseDuration + 0.1f)) {
                     hostState.voices[i].active = false;
                     hostState.voices[i].phase = 0.0f; // Clean reset
                }
            }
        }
    }

    return paContinue;
}
