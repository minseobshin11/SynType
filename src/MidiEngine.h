#pragma once

#include <rtmidi/RtMidi.h>
#include <vector>
#include <mutex>
#include <queue>

struct MidiMessage {
    std::vector<unsigned char> bytes;
    double timestamp;
};

class MidiEngine {
public:
    MidiEngine();
    ~MidiEngine();

    bool init();
    void cleanup();

    // Returns all pending messages since last call
    std::vector<MidiMessage> getPendingMessages();

    // Allows injecting messages manually (e.g. from Python)
    void manualMessage(const std::vector<unsigned char>& bytes);

private:
    static void midiCallback(double deltatime, std::vector< unsigned char > *message, void *userData);

    RtMidiIn* midiin;
    std::mutex queueMutex;
    std::queue<MidiMessage> messageQueue;
    bool initialized;
};
