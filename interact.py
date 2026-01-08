import pysynth
import curses
import time

def main(stdscr):
    # Setup curses
    curses.cbreak()
    stdscr.nodelay(True) # Non-blocking input
    stdscr.clear()
    stdscr.addstr(0, 0, "GPU Synthesizer - Keyboard Control")
    stdscr.addstr(2, 0, "Keys: [a] [s] [d] [f] [g] [h] [j] [k]")
    stdscr.addstr(3, 0, "Notes: C   D   E   F   G   A   B   C'")
    stdscr.addstr(5, 0, "WARNING: Polyphony is limited in terminal mode.")
    stdscr.addstr(6, 0, "         For true piano feel, use 'python3 interact_precise.py'")
    stdscr.addstr(8, 0, "Press 'q' to quit.")

    # Init Synth
    midi = pysynth.MidiEngine()
    if not midi.init():
        stdscr.addstr(7, 0, "Failed to init MIDI (Output might still work)")
        
    audio = pysynth.AudioEngine()
    if not audio.init():
        stdscr.addstr(7, 0, "Failed to init Audio!")
        return

    audio.setMidiEngine(midi)
    audio.start()

    # Key map: char -> MIDI Note
    key_map = {
        'a': 60, # C4
        's': 62, # D4
        'd': 64, # E4
        'f': 65, # F4
        'g': 67, # G4
        'h': 69, # A4
        'j': 71, # B4
        'k': 72  # C5
    }
    
    # Track pressed keys to avoid re-triggering (simulating Note On / Note Off is hard with curses as it doesn't give key-up events easily)
    # Curses only gives key-down. So we will trigger a note and let it ring for a bit, or simulate latching.
    # Typically for a simple synth test, we can just trigger Note On.
    # To do simulated sustain, we might just use a "panic" button or auto-off.
    
    # Better approach for "Piano":
    # Since we can't detect KeyUp in terminal easily, we will make it "monophonic" style or just trigger with fixed duration?
    # NO, we can implement a simple decay or just Toggle?
    # Let's try: Press to play, it plays. It won't stop until you press another key? No that's annoying.
    # Let's just send Note On. And maybe 'z' to stop all?
    
    stdscr.refresh()
    
    active_notes = {} # Map: char -> last_seen_time
    
    stdscr.refresh()
    
    try:
        while True:
            # clear buffer of all pending keys? No, process them all.
            # But we are sleeping 10ms. A fast typer might type faster?
            # Terminal auto-repeat is usually slower (30Hz).
            
            current_time = time.time()
            
            # Process all pending input
            while True:
                try:
                    k = stdscr.getkey()
                    if k == 'q':
                        return # Quit
                    
                    if k in key_map:
                        # If not already active, send Note On
                        if k not in active_notes:
                            note = key_map[k]
                            midi.manualMessage([0x90, note, 100])
                            
                        # Update timestamp
                        active_notes[k] = current_time
                        
                except curses.error:
                    # No more input
                    break
            
            # Check for released keys (timeout)
            # Standard OS repeat delay is ~500ms. We must be larger than that to avoid stutter.
            # This adds release latency, but it's required for curses-based input.
            timeout = 0.6 
            
            keys_to_remove = []
            for k, last_time in active_notes.items():
                if current_time - last_time > timeout:
                    # Note Off
                    note = key_map[k]
                    midi.manualMessage([0x80, note, 0])
                    keys_to_remove.append(k)
            
            for k in keys_to_remove:
                del active_notes[k]

            # Display all active notes
            stdscr.move(8, 0)
            stdscr.clrtoeol()
            if active_notes:
                status_str = "Playing: "
                for k in active_notes:
                    status_str += f"[{k}:{key_map[k]}] "
                stdscr.addstr(status_str)
            else:
                stdscr.addstr("Released")
            
            stdscr.refresh()
            
            time.sleep(0.01)
            
    finally:
        audio.stop()
        audio.cleanup()
        midi.cleanup()

if __name__ == "__main__":
    import os
    # We need to manually invoke curses wrapper to ensure cleanup
    curses.wrapper(main)
