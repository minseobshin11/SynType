#!/bin/bash
export LD_LIBRARY_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/cuda/13.0/targets/x86_64-linux/lib:$LD_LIBRARY_PATH
./gpu_synth
