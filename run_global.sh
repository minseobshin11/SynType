#!/bin/bash
# Helper script to run SynType Global Mode with correct environment variables

# CUDA Runtime Library Path
export LD_LIBRARY_PATH=/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/cuda/13.0/targets/x86_64-linux/lib:$LD_LIBRARY_PATH

# Check for sudo/root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (sudo) to access input devices for global mode."
  echo "Usage: sudo ./run_global.sh"
  exit 1
fi

echo "Starting SynType Global Mode..."
# Use the venv python
./venv/bin/python interact_global.py
