#include <iostream>
#include <thread>
#include <chrono>
#include "AudioEngine.h"
#include "MidiEngine.h"

int main() {
    std::cout << "Starting GPU-Accelerated Synthesizer..." << std::endl;

    try {
        AudioEngine audioEngine;
        MidiEngine midiEngine;
        
        if (!audioEngine.init()) {
            std::cerr << "Failed to initialize Audio Engine." << std::endl;
            return 1;
        }

        if (!midiEngine.init()) {
             std::cerr << "Warning: Failed to initialize MIDI Engine. Continuing without MIDI." << std::endl;
        }

        audioEngine.setMidiEngine(&midiEngine);
        audioEngine.start();

        std::cout << "Synthesizer running. Press Enter to quit..." << std::endl;
        
        // Simple loop to keep main thread alive and maybe print MIDI messages
        // preventing blocking on cin.get() for now to show activity if we wanted
        // but for now let's just use cin.get() as before
        std::cin.get();

        audioEngine.stop();
        midiEngine.cleanup();
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    std::cout << "Exiting..." << std::endl;
    return 0;
}
