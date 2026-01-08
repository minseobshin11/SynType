#include "MidiEngine.h"
#include <iostream>

MidiEngine::MidiEngine() : midiin(nullptr), initialized(false) {}

MidiEngine::~MidiEngine() {
    cleanup();
}

bool MidiEngine::init() {
    try {
        midiin = new RtMidiIn();
    } catch (RtMidiError &error) {
        std::cerr << "RtMidi error: " << error.getMessage() << std::endl;
        return false;
    }

    // Check ports
    unsigned int nPorts = midiin->getPortCount();
    if (nPorts == 0) {
        std::cout << "No MIDI ports available!" << std::endl;
        // Not a fatal error, just no input
        return true; 
    }

    try {
        midiin->openPort(0);
        midiin->setCallback(&MidiEngine::midiCallback, this);
        midiin->ignoreTypes(false, false, false); // Don't ignore sysex, timing, or active sensing for now
    } catch (RtMidiError &error) {
         std::cerr << "RtMidi error opening port: " << error.getMessage() << std::endl;
         return false;
    }

    std::cout << "Opened MIDI port 0: " << midiin->getPortName(0) << std::endl;
    initialized = true;
    return true;
}

void MidiEngine::cleanup() {
    if (midiin) {
        delete midiin;
        midiin = nullptr;
    }
    initialized = false;
}

void MidiEngine::midiCallback(double deltatime, std::vector< unsigned char > *message, void *userData) {
    MidiEngine* engine = (MidiEngine*)userData;
    
    if (message->size() == 0) return;

    MidiMessage msg;
    msg.bytes = *message;
    msg.timestamp = deltatime;

    std::lock_guard<std::mutex> lock(engine->queueMutex);
    engine->messageQueue.push(msg);
    
    // Debug print
    // std::cout << "MIDI: " << (int)msg.bytes[0] << std::endl;
}

void MidiEngine::manualMessage(const std::vector<unsigned char>& bytes) {
    if (bytes.empty()) return;

    MidiMessage msg;
    msg.bytes = bytes;
    msg.timestamp = 0.0; // Immediate

    std::lock_guard<std::mutex> lock(queueMutex);
    messageQueue.push(msg);
}

std::vector<MidiMessage> MidiEngine::getPendingMessages() {
    std::vector<MidiMessage> msgs;
    std::lock_guard<std::mutex> lock(queueMutex);
    while (!messageQueue.empty()) {
        msgs.push_back(messageQueue.front());
        messageQueue.pop();
    }
    return msgs;
}
