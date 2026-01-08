import evdev
from evdev import InputDevice, categorize, ecodes
import sys
import os
import select
import time
import termios
import tty

# Ensure we can import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

def find_keyboard():
    # Attempt to find a keyboard device
    devices = [InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if "keyboard" in device.name.lower():
            return device
    return None

def main():
    print("SynType - Global Generative Typing (evdev)")
    print("Searching for keyboard...")
    
    keyboard = find_keyboard()
    if not keyboard:
        print("No keyboard found! Ensure you have permissions (try sudo).")
        # Fallback to listing all devices
        devices = [InputDevice(path) for path in evdev.list_devices()]
        if not devices:
            print("No input devices found at all. Check /dev/input permissions.")
            return
        print("Available devices:")
        for i, d in enumerate(devices):
            print(f"{i}: {d.path} - {d.name}")
        try:
            sel = int(input("Select device index: "))
            keyboard = devices[sel]
        except:
            return

    print(f"Listening on: {keyboard.name} ({keyboard.path})")
    print("Press TAB to switch modes. Press ESC (on the device) to stop.")
    
    # Disable terminal echo
    set_no_echo()

    synth = SynthController()
    
    # Track modifier keys
    alt_pressed = False

    # Grab exclusive? No, we want to type elsewhere.
    try:
        for event in keyboard.read_loop():
            if event.type == ecodes.EV_KEY:
                key_event = categorize(event)
                
                # Update Alt state
                if key_event.scancode in [ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT]:
                    if key_event.keystate == 1: # Down
                        alt_pressed = True
                    elif key_event.keystate == 0: # Up
                        alt_pressed = False
                
                if key_event.scancode == ecodes.KEY_TAB and key_event.keystate == 1:
                    # Ignore mode switch if Alt is held (Windows/Linux Task Switcher)
                    if not alt_pressed:
                        synth.cycle_mode()
                    # Still play the sound for Tab below? 
                    # If we continue here, we skip note_on logic below.
                    # User likely wants sound but NO mode switch.
                    # So we should NOT continue if we just suppressed mode switch.
                    # Actually, if we switched mode, we probably don't want to play a note simultaneously?
                    # The original code had `continue`, implying Tab didn't make a sound, just switched mode.
                    # If Alt is pressed, we want it to make a sound (or be silent) but NOT switch.
                    # Let's let it fall through to make a sound if Alt+Tab, but `continue` if plain Tab (Mode Switch).
                    if not alt_pressed:
                        continue 

                if key_event.keystate == 1: # Down
                    # Convert scancode to string ID
                    k_id = str(key_event.scancode)
                    # Try to use keycode name as seed for consistency
                    seed = str(key_event.keycode) if isinstance(key_event.keycode, str) else str(key_event.scancode)
                    synth.note_on(k_id, seed)
                    
                elif key_event.keystate == 0: # Up
                    k_id = str(key_event.scancode)
                    synth.note_off(k_id)
                    
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        synth.cleanup()
        restore_terminal()

if __name__ == "__main__":
    main()
