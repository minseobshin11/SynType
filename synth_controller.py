import sys
import os
# Ensure we can import local pysynth.so
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pysynth
import random

# Mode definitions
MODE_HARMONIOUS = 0
MODE_MECHANICAL = 1
MODE_8BIT = 2
MODE_CRYSTAL = 3
MODE_SCIFI = 4
MODE_MASSIVE = 5
NUM_MODES = 6

MODES_INFO = [
    "1. Harmonious (Zen) : Turns text into music (Pentatonic, Triangle)",
    "2. Mechanical       : Satisfying clicky typewriter sounds (Noise)",
    "3. 8-Bit Arcade     : Retro Gameboy vibes (Square, Chromatic)",
    "4. Crystal (Glass)  : High-pitched ambient (Sine, High Octave)",
    "5. Sci-Fi           : Low Dystopian Bass (Saw, Low Octave)",
    "6. MASSIVE GPU      : 1024 Oscillators per Key (SuperSaw Texture)"
]

class SynthController:
    def __init__(self):
        self.midi = pysynth.MidiEngine()
        if not self.midi.init():
            print("Failed to init MIDI")
            
        self.audio = pysynth.AudioEngine()
        if not self.audio.init():
            print("Failed to init Audio!")
            exit(1)

        self.audio.setMidiEngine(self.midi)
        self.audio.start()
        
        self.current_mode = MODE_MECHANICAL # Default to Mechanical as requested by user's new pivot? 
        # Actually user liked Harmonious/Mechanical. Let's stick to Harmonious default or what was last set?
        # Let's default to Harmonious.
        self.current_mode = MODE_HARMONIOUS
        self.set_mode(self.current_mode)
        
        # Pentatonic Scale Construction
        self.pentatonic_scale = []
        base_penta = [0, 2, 4, 7, 9] 
        for octave in range(3, 8): # C3 to C7
            base_note = octave * 12
            for interval in base_penta:
                self.pentatonic_scale.append(base_note + interval)
                
        self.active_notes = {} # k_id -> note

    def cleanup(self):
        self.audio.stop()
        self.audio.cleanup()
        self.midi.cleanup()

    def set_mode(self, mode):
        self.current_mode = mode % NUM_MODES
        print(f"\n[Mode]: {MODES_INFO[self.current_mode]}")
        
        # Set waveform
        if self.current_mode == MODE_HARMONIOUS:
            self.audio.setWaveform(3) # Triangle
        elif self.current_mode == MODE_MECHANICAL:
            self.audio.setWaveform(4) # Noise
        elif self.current_mode == MODE_8BIT:
            self.audio.setWaveform(2) # Square
        elif self.current_mode == MODE_CRYSTAL:
            self.audio.setWaveform(0) # Sine
        elif self.current_mode == MODE_SCIFI:
            self.audio.setWaveform(1) # Saw
        elif self.current_mode == MODE_MASSIVE:
            self.audio.setWaveform(5) # SuperSaw

    def cycle_mode(self):
        self.set_mode(self.current_mode + 1)

    def note_on(self, k_id, char_seed=None):
        if k_id in self.active_notes:
            return # Already playing

        # Determine note based on mode
        note = 60
        velocity = 100
        
        # Use string of key as seed if char not provided
        if not char_seed:
            char_seed = k_id
            
        h = hash(char_seed)

        if self.current_mode == MODE_HARMONIOUS:
            note = self.pentatonic_scale[h % len(self.pentatonic_scale)]
            velocity = random.randint(80, 100)
            
        elif self.current_mode == MODE_MECHANICAL:
            note = random.randint(40, 90)
            velocity = 127
            
        elif self.current_mode == MODE_8BIT:
            note = (h % 36) + 48 # C3 to C6
            velocity = 110
            
        elif self.current_mode == MODE_CRYSTAL:
            idx = h % len(self.pentatonic_scale)
            note = self.pentatonic_scale[idx] + 24 
            if note > 108: note = 108
            velocity = 90
            
        elif self.current_mode == MODE_SCIFI:
            note = (h % 24) + 24 # C1 to C3
            velocity = 120
        
        elif self.current_mode == MODE_MASSIVE:
            note = self.pentatonic_scale[h % len(self.pentatonic_scale)]
            velocity = 100
            
        self.midi.manualMessage([0x90, note, velocity])
        self.active_notes[k_id] = note
        print(f"♪ Note On: {note} (Vel {velocity})\r", end='', flush=True)

    def note_off(self, k_id):
        if k_id in self.active_notes:
            note = self.active_notes[k_id]
            self.midi.manualMessage([0x80, note, 0])
            del self.active_notes[k_id]
            print(f"  Note Off: {note}         \r", end='', flush=True)
