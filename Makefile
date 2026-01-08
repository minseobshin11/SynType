CXX := g++
NVCC := nvcc

# Flags
CXXFLAGS := -std=c++17 -Wall -Wextra -O2
NVCCFLAGS := -std=c++17 -O2

# Dependency flags (using pkg-config)
PKG_CONFIG_DEPS := portaudio-2.0 rtmidi
CXXFLAGS += $(shell pkg-config --cflags $(PKG_CONFIG_DEPS))
LDFLAGS += $(shell pkg-config --libs $(PKG_CONFIG_DEPS))
LDFLAGS += -lcudart -L/opt/nvidia/hpc_sdk/Linux_x86_64/25.9/cuda/13.0/targets/x86_64-linux/lib

# Source files
SRCS_CPP := src/main.cpp src/AudioEngine.cpp src/MidiEngine.cpp
SRCS_CU := src/kernels.cu

# Object files
OBJS_CPP := $(SRCS_CPP:.cpp=.o)
OBJS_CU := $(SRCS_CU:.cu=.o)

# Target executable
TARGET := syntype

# Python configuration
PYTHON := $(shell if [ -f ./venv/bin/python ]; then echo ./venv/bin/python; else echo python3; fi)
PYTHON_INCLUDES := $(shell $(PYTHON) -m pybind11 --includes)
PYTHON_SUFFIX := $(shell $(PYTHON) -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")
TARGET_LIB := pysynth$(PYTHON_SUFFIX)

.PHONY: all clean python

all: $(TARGET)

python: $(TARGET_LIB)

$(TARGET): $(OBJS_CPP) $(OBJS_CU)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

$(TARGET_LIB): src/bindings.cpp $(OBJS_CU) src/AudioEngine.o src/MidiEngine.o
	$(CXX) $(CXXFLAGS) -O3 -shared -fPIC $(PYTHON_INCLUDES) -o $@ $^ $(LDFLAGS)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -fPIC -c $< -o $@

%.o: %.cu
	$(NVCC) $(NVCCFLAGS) -Xcompiler -fPIC -c $< -o $@

clean:
	rm -f $(OBJS_CPP) $(OBJS_CU) $(TARGET) $(TARGET_LIB)
