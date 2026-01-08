#include "kernels.h"
#include <cuda_runtime.h>
#include <math_constants.h>
#include <iostream>

SynthState* d_state = nullptr;
float* d_output = nullptr;
unsigned int currentBufferSize = 0;

__global__ void synthKernel(float* output, SynthState* state, unsigned long frames, float sampleRate) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx < frames) {
        float sampleL = 0.0f;
        float sampleR = 0.0f;
        
        float timeStep = 1.0f / sampleRate;

        // Iterate over voices (naive approach, fast enough for 32 voices)
        for (int v = 0; v < MAX_VOICES; ++v) {
            Voice& voice = state->voices[v];
            if (voice.active) {
                // Calculate time for this sample relative to the buffer start + stored phase?
                // Problem: Phase needs to be continuous across buffers.
                // We should update the phase in global memory or calculate it from absolute time.
                // Updating global memory per sample is bad. 
                // Better approach: 
                // 1. Load phase at start.
                // 2. Compute samples.
                // 3. Store phase back? (Race condition if modifying state in parallel?)
                // Alternative: Parallelize by sample, so each thread computes one sample.
                // Phase = startPhase + idx * frequency * 2PI / SR.
                // But we need to write back the end phase for the next buffer.
                
                // For simplicity in this step:
                // We will assume 'voice.phase' is the phase at the start of THIS buffer.
                // The CPU will update voice.phase += frequency * 2PI * bufferSize / SR after the kernel.
                // Wait, CPU updating phase after kernel is tricky if they run async.
                // Let's do it on GPU. One thread (e.g. idx 0) updates the phase for the next frame? 
                // Calculate Envelope
                float env = 0.0f;
                // Simple Attack-Release
                float attack = 0.01f; // Fast attack default
                float sustain = 1.0f;
                float rel = 0.05f;    // Fast release default
                
                // Orchestral Mode (Massive) needs slow attack/release
                if (state->waveform == 5) {
                     attack = 0.5f; // 500ms slow swell
                     rel = 1.0f;    // 1s long tail
                }

                float t = voice.noteTime + idx * timeStep;
                
                // Envelope Logic
                if (state->waveform == 4) {
                    // Mechanical Mode: One-shot percussive click (ignoring hold/release)
                    // Sharp attack, super fast decay to silence
                    float clickDur = 0.05f; // 50ms total
                    if (t < clickDur) {
                        // Linear decay from 1.0 to 0.0
                        env = 1.0f - (t / clickDur);
                        // Make it curve a bit? Power of 2 makes it snappier
                        env = env * env; 
                    } else {
                        env = 0.0f;
                    }
                } else if (!voice.release) {
                    // Normal Attack / Sustain phase
                    if (t < attack) {
                        env = t / attack;
                    } else {
                        env = sustain;
                    }
                } else {
                    // Normal Release phase
                    // Time since release started
                    float rTime = t - voice.releaseTime; 
                    if (rTime < rel) {
                         env = sustain * (1.0f - rTime / rel);
                    } else {
                         env = 0.0f;
                    }
                }
                
                if (env < 0.0f) env = 0.0f;

                
                // Phase Logic
                float currentPhase = voice.phase + (float)idx * (voice.frequency * 2.0f * CUDART_PI_F * timeStep);
                // Wrap phase to 0..2PI for calculation (though sinf handles large values, others might not)
                float p = fmodf(currentPhase, 2.0f * CUDART_PI_F);
                
                float val = 0.0f;
                switch (state->waveform) {
                    case 0: // Sine
                        val = sinf(p);
                        break;
                    case 1: // Sawtooth
                        // 0..2PI -> -1..1
                        val = 1.0f - (p * (1.0f / CUDART_PI_F));
                        break;
                    case 2: // Square
                        val = (p < CUDART_PI_F) ? 1.0f : -1.0f;
                        break;
                    case 3: // Triangle
                        if (p < CUDART_PI_F) {
                            val = 1.0f - (p * (2.0f / CUDART_PI_F));
                        } else {
                            val = -1.0f + ((p - CUDART_PI_F) * (2.0f / CUDART_PI_F));
                        }
                        break;
                    case 4: // Noise (Pseudo-random hash)
                        {
                            unsigned int seed = (unsigned int)(idx + (unsigned long long)currentPhase * 1000);
                            seed = (seed ^ 61) ^ (seed >> 16);
                            seed *= 9;
                            seed = seed ^ (seed >> 4);
                            seed *= 0x27d4eb2d;
                            seed = seed ^ (seed >> 15);
                            // Normalize 0..UINT_MAX to -1..1
                            val = ((float)seed / (float)0xFFFFFFFF) * 2.0f - 1.0f;
                        }
                        break;
                    case 5: // Massive SuperSaw (1024 Oscillators per voice)
                        {
                            // FIX: Use absolute time to calculate phase to prevent discontinuity when detuning
                            float absTime = voice.noteTime + idx * timeStep;
                            float baseAbsPhase = absTime * voice.frequency * 2.0f * CUDART_PI_F;

                            // We sum 1024 slightly detuned sawtooth waves.
                            float acc = 0.0f;
                            int numOscs = 1024;
                            for (int k = 0; k < numOscs; ++k) {
                                // Random Hash for this oscillator
                                unsigned int h = k * 1664525u + 1013904223u;
                                // Secondary hash for detune to uncouple it from phase offset
                                unsigned int h2 = (h ^ 0x27d4eb2d) * 9;

                                // FIX 3: Randomized Detune to avoid "Sticky" comb-filtering (spectral beak)
                                // Range: +/- 3% (0.97 to 1.03) with random distribution instead of linear
                                float randomDetune = 1.0f + (((float)(h2 % 10000) / 10000.0f) - 0.5f) * 0.06f; 
                                
                                // FIX 2: Random Phase Offset (Already applied)
                                float randomOffset = ((float)h / 4294967296.0f) * 2.0f * CUDART_PI_F;
                                
                                // Calculate phase using Absolute Time + Random Detune + Random Offset
                                float detunedPhase = baseAbsPhase * randomDetune + randomOffset;
                                
                                // Wrap locally
                                float p = fmodf(detunedPhase, 2.0f * CUDART_PI_F);
                                
                                // Sawtooth math: 1.0 - (phase / PI)
                                acc += 1.0f - (p / CUDART_PI_F);
                            }
                            
                            // FIX 1: Volume Normalization
                            // Incoherent sum grows as sqrt(N). sqrt(1024) = 32.
                            // Previously 1/1024 was too quiet. 
                            // We use 20.0f gain factor to compensate (leaving headroom).
                            val = (acc / numOscs) * 20.0f; 
                        }
                        break;
                    default:
                        val = sinf(p);
                }
                
                sampleL += val * voice.velocity * env;
                sampleR += val * voice.velocity * env;
            }
        }

        // Write stereo interleaved
        output[idx * 2] = sampleL * state->masterVolume;
        output[idx * 2 + 1] = sampleR * state->masterVolume;
    }
    
    // Update phases for next buffer - only one thread per voice should do this
    // But we are parallelizing over samples.
    // Let's use a separate kernel or do it at the end of buffer processing?
    // Actually, simplest is to let CPU handle phase tracking for now to ensure consistency,
    // OR have a small kernel launch to update phases.
}

// Phase update moved to CPU



bool initCUDA(unsigned int bufferSize) {
    currentBufferSize = bufferSize;
    size_t outSize = bufferSize * 2 * sizeof(float); 
    size_t stateSize = sizeof(SynthState);

    cudaError_t err = cudaMalloc(&d_output, outSize);
    if (err != cudaSuccess) {
        std::cerr << "cudaMalloc output failed: " << cudaGetErrorString(err) << std::endl;
        return false;
    }

    err = cudaMalloc(&d_state, stateSize);
    if (err != cudaSuccess) {
        std::cerr << "cudaMalloc state failed: " << cudaGetErrorString(err) << std::endl;
        return false;
    }
    
    return true;
}

void cleanupCUDA() {
    if (d_output) cudaFree(d_output);
    if (d_state) cudaFree(d_state);
    d_output = nullptr;
    d_state = nullptr;
}

void updateStateCUDA(const SynthState& hostState) {
    if (!d_state) return;
    cudaMemcpy(d_state, &hostState, sizeof(SynthState), cudaMemcpyHostToDevice);
}

void processAudioCUDA(float* output, unsigned long frames, float time) {
    if (!d_output || !d_state) return;

    int threadsPerBlock = 256;
    int blocksPerGrid = (frames + threadsPerBlock - 1) / threadsPerBlock;

    synthKernel<<<blocksPerGrid, threadsPerBlock>>>(d_output, d_state, frames, 44100.0f);
    
    // Drawback: CPU tracks phase and time now. GPU just renders.
    
    // Copy result back to host
    cudaMemcpy(output, d_output, frames * 2 * sizeof(float), cudaMemcpyDeviceToHost);
}
