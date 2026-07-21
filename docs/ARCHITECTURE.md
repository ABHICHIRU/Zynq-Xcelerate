# Zynq-Xcelerate: Hardware-Software Co-Design Architecture

> Cross-reference document linking the FPGA RTL implementation (`verilog_implementation_main_model`) with the ML pipeline (`production-elite-2d`).

---

## Overview

The Zynq-Xcelerate system is a hardware-software co-design targeting the Xilinx Zynq-7020 SoC. The design is split across two interdependent branches:

| Branch | Purpose | Contents |
|:---|:---|:---|
| [`production-elite-2d`](https://github.com/ABHICHIRU/Zynq-Xcelerate/tree/production-elite-2d) | ML model development | Training pipeline, 2D inference engine, data generation, benchmarking, and validation scripts |
| [`verilog_implementation_main_model`](https://github.com/ABHICHIRU/Zynq-Xcelerate/tree/verilog_implementation_main_model) | FPGA RTL synthesis | Synthesizable Verilog modules for the inference accelerator, voting logic, memory subsystem, and SoC integration |

---

## RTL ↔ Python Mapping

| Python Module (production-elite-2d) | Verilog RTL (this branch) | Function |
|:---|:---|:---|
| `src/core/backbone_2d.py` | `rtl/core/ml_accelerator_wrapper.v` | Feature extraction backbone |
| `src/core/heads_2d.py` (threat) | `rtl/core/threat_detector_rtl.v` | Threat binary classification |
| `src/core/heads_2d.py` (type) | `rtl/core/type_classifier_rtl.v` | 3-class type identification |
| `src/core/heads_2d.py` (jammer) | `rtl/core/jammer_detector_rtl.v` | Jammer isolation |
| `src/core/voting_logic.py` | `rtl/core/voting_module_rtl.v` | Multi-head decision fusion |
| `src/utils/channelizer.py` | *(PS-side or HLS)* | STFT / Polyphase channelizer |
| `src/data_pipeline/production_stream.py` | `rtl/memory/data_input_fifo.v` | Real-time data ingestion |

---

## Quantization & Weight Export

The INT8 quantized model is generated on the `production-elite-2d` branch and consumed by this branch for BRAM initialization. The quantization formula is:

$$x_{\text{fixed}} = \frac{\text{clip}\left(\text{round}(x \cdot 127),\; -128,\; 127\right)}{127.0}$$

Weight export to `.coe` (Xilinx coefficient) format or C header arrays for BRAM initialization should be performed as part of the deployment flow.

---

## Development Workflow

1. **ML Development** — Work on `production-elite-2d`. Train, validate, and export INT8 models.
2. **RTL Development** — Work on `verilog_implementation_main_model`. Implement and simulate Verilog modules.
3. **Integration** — Export quantized weights from the ML branch → import into RTL testbenches on this branch.
4. **Verification** — Run Python simulation (`scripts/validation/`) to generate golden reference outputs. Compare against RTL simulation results.
