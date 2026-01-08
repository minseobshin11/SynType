# SynType 🌊🎹
> *Formerly GPU-Accelerated Synthesizer*

A real-time, low-latency synthesizer that turns your typing into music and sound effects. Powered by **CUDA** for massive polyphony and **Python** for flexible control.

Transform your keyboard into a fast, responsive instrument with 5 unique generative modes.

## features

*   **Zero-Latency Response**: Uses `pynput` and C++ bindings for immediate audio feedback.
*   **GPU DSP**: All 32+ voices are synthesized in parallel using NVIDIA CUDA kernels.
*   **5 Generative Modes**: From ambient Zen music to clicky mechanical switches.
*   **Full Keyboard Support**: Every key (letters, numbers, tabs, modifiers) produces sound.

## Modes

Press **`Tab`** to cycle through modes:

1.  **Harmonious (Zen)** 🧘
    *   *Sound*: Soft Triangle / Sine waves.
    *   *Logic*: Maps all inputs to a C Major Pentatonic scale. No matter what you type, it creates a soothing, musical melody.
2.  **Mechanical (Typewriter)** ⌨️
    *   *Sound*: Crisp noise bursts.
    *   *Logic*: Random pitch variations to simulate distinct switch sounds. Satisfying "thock".
3.  **8-Bit Arcade** 👾
    *   *Sound*: Square waves.
    *   *Logic*: Chromatic/Random mapping. Sounds like a retro game console.
4.  **Crystal (Glass)** 🔮
    *   *Sound*: High-pitched Sine waves.
    *   *Logic*: High-octave pentatonic chimes.
5.  **Sci-Fi (Dystopian)** 🛸
    *   *Sound*: Low Sawtooth drones.
    *   *Logic*: Deep bass rumbles for a cinematic feel.
6.  **MASSIVE GPU (SuperSaw)** 🚀
    *   *Sound*: Thick, lush, detuned synthesizer wall-of-sound.
    *   *Logic*: **1,024 Oscillators per Key**. Demonstrates raw GPU power. A 10-finger chord generates 10,240 oscillators in real-time.

## Setup Requirements

### Hardware
*   NVIDIA GPU (CUDA Capable)
*   Linux OS (Tested on x86_64)

### Software
*   **CUDA Toolkit** (11.0+)
*   **GCC / G++**
*   **Python** (3.8+)
*   **PortAudio** (Development headers)
*   **RtMidi** (Development headers)

#### Install Dependencies (Ubuntu/Debian)
```bash
sudo apt-get install libportaudio2 portaudio19-dev librtmidi-dev python3-dev
```

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/gpu-synth.git
    cd gpu-synth
    ```

2.  **Set up Python Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install pynput pybind11
    ```

3.  **Build the Engine**:
    Run `make` to compile the C++ core and Python bindings.
    ```bash
    make clean && make python
    ```
    *This creates `pynput.so` (the extension) in the current directory.*

## Usage

### 1. Global Background Mode (Recommended) 🌍
This mode runs in the background, listening to key events globally (kernel level). It works even if you are browsing the web or coding in another window.

**Features:**
*   **Privacy First**: Visual feedback shows music notes (e.g., "Note On: 64") instead of the keys you type.
*   **Input Suppression**: Typing in the terminal window itself is hidden while running, keeping your screen clean.
*   **Alt+Tab Friendly**: Holding Alt suppresses the Tab mode switch, so you can switch windows without changing the instrument.

**Run Command:**
```bash
# Helper script handles sudo and environment variables for you:
sudo ./run_global.sh
```

### 2. Focused Mode (Legacy)
Only works when the terminal window is active.
```bash
# Must set LD_LIBRARY_PATH manually
export LD_LIBRARY_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/cuda/13.0/targets/x86_64-linux/lib:$LD_LIBRARY_PATH
./venv/bin/python3 interact_precise.py
```

---

## Modes

Press **`Tab`** to cycle through 6 distinct generative environments:

1.  **Harmonious (Zen)** 🧘
    *   *Sound*: Soft Triangle waves.
    *   *Logic*: **Pentatonic Scale**. No matter what you type, it produces a consonant, musical melody. Perfect for flow state.
2.  **Mechanical (Typewriter)** ⌨️
    *   *Sound*: Crisp, percussive clicks (Noise).
    *   *Physics*: **One-Shot Envelope**. Mimics a physical switch with a sharp 50ms decay. Highly tactile and satisfying.
3.  **8-Bit Arcade** 👾
    *   *Sound*: Square waves.
    *   *Logic*: Chromatic mapping. Sounds like a retro Gameboy soundtrack.
4.  **Crystal (Glass)** 🔮
    *   *Sound*: Sine waves (High Octave).
    *   *Logic*: Ethereal chimes for a delicate atmosphere.
5.  **Sci-Fi (Dystopian)** 🛸
    *   *Sound*: Sawtooth drones (Low Octave).
    *   *Logic*: Deep, rumbling bass textures.
6.  **MASSIVE GPU (Orchestral)** 🎻
    *   *Sound*: Thick, luscious SuperSaw pads.
    *   *Physics*: **ADSR Envelopes**. Notes swell in slowly (500ms attack) and fade out gracefully (1s release). 
    *   *Power*: **1,024 Oscillators per Key**. A simple 3-note chord generates 3,072 oscillators in real-time, showcasing raw GPU parallel processing.

---

## Under the Hood: Hybrid Architecture

To achieve low-latency massive polyphony with complex envelopes, this project uses a hybrid split:

*   **CPU (The Conductor)**: 
    *   Manages user input and MIDI events.
    *   Tracks note lifecycles (Attack, Decay, Release).
    *   Calculates Phase continuity to prevent clicking.
*   **GPU (The Orchestra)**: 
    *   Receives state snapshots every audio buffer.
    *   Executes heavy DSP: Waveform generation, detuning, and summing thousands of oscillators in parallel.

## Troubleshooting

### "ModuleNotFoundError: No module named 'pysynth'"
This often happens when running with `sudo`. The script automatically handles this by appending the local path, but ensure you run from the project root.

### "Keys not working when pressing 3+ at once"
This is **Keyboard Ghosting**. Most standard USB keyboards cannot register more than ~2-6 specific keys simultaneously. For full polyphony, use a **Mechanical Keyboard with N-Key Rollover (NKRO)**.
