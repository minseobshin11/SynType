#include "SharedState.h"

bool initCUDA(unsigned int bufferSize);
void cleanupCUDA();
void updateStateCUDA(const SynthState& hostState);
void processAudioCUDA(float* output, unsigned long frames, float time);
