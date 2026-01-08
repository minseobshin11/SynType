#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "AudioEngine.h"
#include "MidiEngine.h"

namespace py = pybind11;

PYBIND11_MODULE(pysynth, m) {
    m.doc() = "GPU-Accelerated Synthesizer Python Bindings";

    py::class_<MidiEngine>(m, "MidiEngine")
        .def(py::init<>())
        .def("init", &MidiEngine::init)
        .def("cleanup", &MidiEngine::cleanup)
        .def("manualMessage", &MidiEngine::manualMessage);

    py::class_<AudioEngine>(m, "AudioEngine")
        .def(py::init<>())
        .def("init", &AudioEngine::init)
        .def("start", &AudioEngine::start)
        .def("stop", &AudioEngine::stop)
        .def("cleanup", &AudioEngine::cleanup)
        .def("setMidiEngine", &AudioEngine::setMidiEngine)
        .def("setWaveform", &AudioEngine::setWaveform);
}
