import pysynth
import time

def main():
    print("Initializing GPU Synthesizer via Python...")
    
    midi = pysynth.MidiEngine()
    if not midi.init():
        print("Failed to init MIDI")
        
    audio = pysynth.AudioEngine()
    if not audio.init():
        print("Failed to init Audio")
        return

    audio.setMidiEngine(midi)
    
    print("Starting Audio Stream...")
    audio.start()
    
    print("Playing test tone (C4) for 2 seconds...")
    # Simulate Note On: Channel 1, Note 60 (C4), Velocity 100
    midi.manualMessage([0x90, 60, 100])
    time.sleep(2)
    
    print("Stopping test tone...")
    # Simulate Note Off: Channel 1, Note 60, Velocity 0
    midi.manualMessage([0x80, 60, 0])
    
    print("Running for 3 more seconds. Play your MIDI keyboard if you have one!")
    time.sleep(3)
    
    print("Stopping...")
    audio.stop()
    audio.cleanup()
    midi.cleanup()
    print("Done.")

if __name__ == "__main__":
    main()
