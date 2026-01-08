import sys
import termios
import tty
from pynput import keyboard
from synth_controller import SynthController

# Save terminal settings
try:
    orig_settings = termios.tcgetattr(sys.stdin)
except:
    orig_settings = None

def set_no_echo():
    if orig_settings:
        tty.setcbreak(sys.stdin.fileno())

def restore_terminal():
    if orig_settings:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, orig_settings)
    print("\nStopped.")

synth = SynthController()
running = True

def on_press(key):
    global running
    try:
        k_id = str(key)
        
        if key == keyboard.Key.tab:
             synth.cycle_mode()
             return

        if key == keyboard.Key.esc:
            return False
            
        # Determine seed
        char_seed = k_id
        if hasattr(key, 'char') and key.char:
            char_seed = key.char
            
        synth.note_on(k_id, char_seed)

    except Exception as e:
        print(e)
        
def on_release(key):
    global running
    try:
        k_id = str(key)
        
        if key == keyboard.Key.esc:
             running = False
             return False

        synth.note_off(k_id)

    except Exception as e:
        print(e)

print("GPU Synthesizer - Precise Keyboard Control")
print("Controls:")
print("  [Tab]               : Switch Mode")
print("  [ESC]               : Quit")
print("Modes checked in synth_controller.")
print("Press ESC to quit.")

# Set no echo
set_no_echo()

# Non-blocking listener
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

try:
    while running:
        import time
        time.sleep(0.1)
        if not listener.is_alive():
            running = False
finally:
    synth.cleanup()
    restore_terminal()

        

