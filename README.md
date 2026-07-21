# Zynq-Xcelerate: FPGA RTL Implementation for RF Anomaly Detection on Zynq-7020 SoC

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)
[![Verilog RTL](https://img.shields.io/badge/HDL-Verilog-purple.svg)](#)
[![Branch: verilog_implementation_main_model](https://img.shields.io/badge/branch-verilog__impl-brightgreen.svg)](#)

---

## Abstract

This branch contains the **Register-Transfer Level (RTL) implementation** of the Zynq-Xcelerate RF anomaly detection system, targeting the [Xilinx Zynq-7020 SoC FPGA](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html). The design implements a hardware-accelerated multi-head neural network inference engine with integrated signal tracking, voting logic, and power management — enabling real-time classification of RF threats at sub-millisecond latencies.

This branch is **interdependent** with the ML model development on [`production-elite-2d`](https://github.com/ABHICHIRU/Zynq-Xcelerate/tree/production-elite-2d), which provides the training pipeline, quantized model weights, and golden reference outputs for RTL verification.

> **ML Pipeline Branch:** See [`production-elite-2d`](https://github.com/ABHICHIRU/Zynq-Xcelerate/tree/production-elite-2d) for the complete training, inference, and validation pipeline.

---

## Table of Contents

- [System Architecture](#system-architecture)
- [RTL Module Hierarchy](#rtl-module-hierarchy)
- [Technical Specifications](#technical-specifications)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Hardware-Software Co-Design Workflow](#hardware-software-co-design-workflow)
- [ML Model Architecture (Python Reference)](#ml-model-architecture-python-reference)
- [References](#references)

---

## System Architecture

The Zynq-7020 SoC partitions processing between the Processing System (PS) — a dual-core ARM Cortex-A9 — and the Programmable Logic (PL) fabric. The Zynq-Xcelerate design leverages both:

- **PS (ARM):** Handles I/Q data ingestion, STFT channelization, and high-level control.
- **PL (FPGA):** Executes the quantized neural network inference, multi-head classification, voting logic, and real-time signal tracking.

### SoC Block Diagram

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        ZYNQ-7020 SoC                                    │
│                                                                         │
│  ┌─────────────────────┐         ┌─────────────────────────────────────┐│
│  │   Processing System │         │      Programmable Logic (PL)        ││
│  │   (ARM Cortex-A9)   │   AXI   │                                     ││
│  │                     │◄───────►│  ┌────────────┐  ┌──────────────┐  ││
│  │  • I/Q Ingestion    │         │  │ Control    │  │ Input Buffer │  ││
│  │  • STFT Bridge      │         │  │ Registers  │  │ RAM + FIFO   │  ││
│  │  • Linux / Bare-    │         │  └──────┬─────┘  └──────┬───────┘  ││
│  │    metal driver     │         │         │               │          ││
│  │  • Result logging   │         │  ┌──────▼───────────────▼───────┐  ││
│  │                     │         │  │    ML Accelerator Wrapper    │  ││
│  └─────────────────────┘         │  │    (INT8 Inference Engine)   │  ││
│                                  │  └──────────────┬──────────────┘  ││
│                                  │          ┌──────┼──────┐          ││
│                                  │          │      │      │          ││
│                                  │     ┌────▼──┐┌──▼───┐┌─▼─────┐   ││
│                                  │     │Threat ││Type  ││Jammer │   ││
│                                  │     │Detect ││Class ││Detect │   ││
│                                  │     └───┬───┘└──┬───┘└───┬───┘   ││
│                                  │         └───────┼────────┘       ││
│                                  │          ┌──────▼──────┐         ││
│                                  │          │ Voting      │         ││
│                                  │          │ Module      │         ││
│                                  │          └──────┬──────┘         ││
│                                  │          ┌──────▼──────┐         ││
│                                  │          │ Output      │         ││
│                                  │          │ Aggregator  │         ││
│                                  │          └──────┬──────┘         ││
│                                  │          ┌──────▼──────┐         ││
│                                  │          │ Tracking    │         ││
│                                  │          │ Engine      │         ││
│                                  │          └─────────────┘         ││
│                                  │                                   ││
│                                  │  ┌─────────────┐ ┌─────────────┐ ││
│                                  │  │RF Frontend  │ │Power        │ ││
│                                  │  │Control      │ │Control      │ ││
│                                  │  └─────────────┘ └─────────────┘ ││
│                                  └─────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

---

## RTL Module Hierarchy

All Verilog source files are organized under the `rtl/` directory with the following structure:

### Top-Level Integration (`rtl/top/`)

| Module | File | Description |
|:---|:---|:---|
| **SkyShield v4.2** | `skyshield_v42_top.v` | Primary top-level wrapper — instantiates all subsystems, AXI interconnect, and clock/reset management |
| **SkyShield AI v3** | `top_skyshield_ai_v3.v` | Full AI subsystem integration with extended peripheral support |
| **SkyShield AI v3 Lite** | `top_skyshield_ai_v3_simplified.v` | Resource-reduced variant for minimal deployments |

### Inference Core (`rtl/core/`)

| Module | File | Description |
|:---|:---|:---|
| **ML Accelerator** | `ml_accelerator_wrapper.v` | AXI-wrapped inference engine — manages weight loading from BRAM, MAC operations, and activation functions |
| **Threat Detector** | `threat_detector_rtl.v` | Binary classification head: benign (WiFi) vs. threat (Drone/Jammer) |
| **Type Classifier** | `type_classifier_rtl.v` | Multi-class head: WiFi / DJI UAV Telemetry / Electronic Warfare Jammer |
| **Jammer Detector** | `jammer_detector_rtl.v` | Dedicated binary head for high-entropy jammer isolation |
| **Voting Module** | `voting_module_rtl.v` | Multi-head decision fusion — generates hardware response codes from classification outputs |

### Memory Subsystem (`rtl/memory/`)

| Module | File | Description |
|:---|:---|:---|
| **Input Buffer RAM** | `input_buffer_ram.v` | Dual-port BRAM for incoming I/Q sample storage |
| **Output Buffer RAM** | `output_buffer_ram.v` | Classification result buffer before PS readback |
| **Data Input FIFO** | `data_input_fifo.v` | Streaming FIFO for continuous I/Q data ingestion from the ADC/DMA interface |

### Peripherals & Control (`rtl/peripherals/`)

| Module | File | Description |
|:---|:---|:---|
| **Control Registers** | `control_registers.v` | AXI-Lite register file for PS↔PL runtime configuration and status monitoring |
| **RF Frontend Control** | `rf_frontend_control.v` | SPI/GPIO interface for RF tuner gain, frequency, and ADC control |
| **Output Aggregator** | `output_aggregator.v` | Collects classification outputs from all heads and formats for DMA transfer |
| **Power Control** | `power_control.v` | Clock gating, power domain management, and low-power mode control |
| **Tracking Engine** | `tracking_engine.v` | Signal tracking FSM — maintains persistent threat state across inference windows |

---

## Technical Specifications

| Parameter | Specification |
|:---|:---|
| **Target FPGA** | Xilinx Zynq-7020 (XC7Z020-CLG484) |
| **Clock Domain** | 100 MHz (PL fabric) |
| **Data Width** | 8-bit fixed-point (INT8) |
| **Input Interface** | AXI4-Stream (I/Q data from PS DMA) |
| **Control Interface** | AXI4-Lite (register access from PS) |
| **BRAM Usage** | ~450 KB (model weights + buffers) |
| **Target Latency** | < 1.2 ms per inference |
| **Classification Heads** | 3 (Threat, Type, Jammer) |

---

## Repository Structure

```
Zynq-Xcelerate/                        (verilog_implementation_main_model branch)
│
├── README.md                           # This file
├── main.py                             # ML training entry point
├── .gitignore
│
├── rtl/                                # ★ Synthesizable Verilog RTL modules
│   ├── top/                            #   Top-level integration
│   │   ├── skyshield_v42_top.v
│   │   ├── top_skyshield_ai_v3.v
│   │   └── top_skyshield_ai_v3_simplified.v
│   ├── core/                           #   Inference engine & classification heads
│   │   ├── ml_accelerator_wrapper.v
│   │   ├── threat_detector_rtl.v
│   │   ├── type_classifier_rtl.v
│   │   ├── jammer_detector_rtl.v
│   │   └── voting_module_rtl.v
│   ├── memory/                         #   BRAM buffers & FIFOs
│   │   ├── input_buffer_ram.v
│   │   ├── output_buffer_ram.v
│   │   └── data_input_fifo.v
│   └── peripherals/                    #   Control, power, & tracking
│       ├── control_registers.v
│       ├── rf_frontend_control.v
│       ├── output_aggregator.v
│       ├── power_control.v
│       └── tracking_engine.v
│
├── docs/                               # Technical documentation
│   ├── ARCHITECTURE.md                 # Cross-reference — ML ↔ RTL co-design
│   ├── BENCHMARK_REPORT_2D.md          # ML benchmark results
│   └── instruction.md                  # Data generation specification
│
├── assets/                             # Visualization outputs & figures
│   ├── spectrogram_comparison.png
│   ├── viz_2d_samples.png
│   ├── viz_heads_2d.png
│   ├── viz_model_jammer.png
│   ├── viz_model_threat.png
│   ├── viz_model_type.png
│   └── viz_raw_1d_physics.png
│
├── src/                                # Core Python library (ML reference)
│   ├── core/                           #   Model architecture definitions
│   ├── data_pipeline/                  #   Data generation & loading
│   ├── training/                       #   Training pipeline
│   └── utils/                          #   Utility functions
│
├── scripts/                            # Standalone executable scripts
│   ├── training/                       #   Model training
│   ├── visualization/                  #   Plotting & visualization
│   ├── benchmarking/                   #   Performance benchmarking
│   ├── validation/                     #   End-to-end validation
│   ├── analysis/                       #   Data analysis
│   └── pipeline/                       #   Production pipeline variants
│
├── models/                             # Trained model weights (.pth)
├── data/                               # Datasets (.npz, .npy)
├── demo_samples/                       # Pre-generated demo signals
├── templates/                          # Web UI templates
├── viz_metrics/                        # Training metric visualizations
└── logs/                               # Training logs & captured data
```

---

## Getting Started

### Prerequisites

- **Synthesis:** Xilinx Vivado Design Suite ≥ 2020.2
- **Python ML:** Python ≥ 3.12, PyTorch ≥ 2.0, NumPy, SciPy

### Clone & Setup

```bash
git clone https://github.com/ABHICHIRU/Zynq-Xcelerate.git
cd Zynq-Xcelerate
git checkout verilog_implementation_main_model
```

### Vivado Project Setup

1. Open Vivado and create a new project targeting `xc7z020clg484-1`.
2. Add all files under `rtl/` as design sources.
3. Set `rtl/top/skyshield_v42_top.v` as the top module.
4. Run synthesis and implementation.

---

## Hardware-Software Co-Design Workflow

```text
[production-elite-2d branch]              [verilog_implementation_main_model branch]
         │                                              │
    Train Model                                    RTL Design
         │                                              │
    Export INT8                                    Simulate in
    Weights (.pth)                                 Vivado/Verilator
         │                                              │
    Generate Golden ─────────────────────────► Compare with
    Reference Outputs                           RTL Simulation
         │                                              │
         └──────────── Integration ────────────────────┘
                           │
                    Vivado Bitstream
                    Generation + SoC
                    Deployment
```

1. **Train & Quantize** on `production-elite-2d` → export INT8 weights.
2. **Convert weights** to `.coe` / C header format for BRAM initialization.
3. **Synthesize & Simulate** on this branch → verify against Python golden references.
4. **Deploy** bitstream to Zynq-7020 hardware.

---

## ML Model Architecture (Python Reference)

The Python reference implementation of the neural network is maintained in the `src/` directory. Key correspondences between Python modules and Verilog RTL:

| Python Module | Verilog RTL | Function |
|:---|:---|:---|
| `src/core/backbone.py` | `rtl/core/ml_accelerator_wrapper.v` | Shared feature extraction backbone |
| `src/core/heads.py` (threat) | `rtl/core/threat_detector_rtl.v` | Threat binary classification |
| `src/core/heads.py` (type) | `rtl/core/type_classifier_rtl.v` | 3-class type identification |
| `src/core/heads.py` (jammer) | `rtl/core/jammer_detector_rtl.v` | Jammer isolation |
| `src/core/voting_logic.py` | `rtl/core/voting_module_rtl.v` | Multi-head decision fusion |
| `src/data_pipeline/production_stream.py` | `rtl/memory/data_input_fifo.v` | Real-time data ingestion |

### Model Specifications

| Parameter | Specification |
|:---|:---|
| **Total Parameters** | 340,709 |
| **Input Tensor** | 2 × 512 (I/Q Time-Domain) |
| **Quantization** | INT8 Hardware-Aware |
| **BRAM Footprint** | ~341 KB (57% of Zynq-7020 BRAM) |
| **Inference Latency** | 0.08 ms/sample (CPU baseline) |

### Waveform Synthesis Models

- **WiFi (IEEE 802.11b):** 11-chip Barker sequence DSSS spreading.
- **UAV Telemetry (DJI Pulse):** Multitone carriers with Gaussian-smoothed rectangular envelopes.
- **Electronic Warfare (Wiener Jammer):** Frequency-sweeping chirps with Wiener-process phase noise.

---

## References

1. **O'Shea, T. J., & Hoydis, J. (2017).** ["An Introduction to Deep Learning for the Physical Layer."](https://ieeexplore.ieee.org/document/7924307) *IEEE Transactions on Cognitive Communications and Networking*, 3(4), 563–575.
2. **Jacob, B., et al. (2018).** ["Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference."](https://openaccess.thecvf.com/content_cvpr_2018/html/Jacob_Quantization_and_Training_CVPR_2018_paper.html) *CVPR*.
3. **Caruana, R. (1997).** "Multitask Learning." *Machine Learning*, 28(1), 41–75.
4. **Tse, D., & Viswanath, P. (2005).** [*Fundamentals of Wireless Communication*](https://web.stanford.edu/~dntse/Chapters_PDF/Fundamentals_Wireless_Communication_chapter1.pdf). Cambridge University Press.
5. **Duarte, M., et al. (2018).** ["Fast inference of deep neural networks in FPGAs for particle physics."](https://arxiv.org/abs/1804.06913) *JINST* — Core principles for [hls4ml](https://fastmachinelearning.org/hls4ml/).

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

*This project is intended for defensive research and academic study within the context of FPGA-accelerated signal intelligence. The authors bear no responsibility for misuse of the techniques or implementations described herein.*

---

**Maintained by:** [ABHICHIRU](https://github.com/ABHICHIRU)  
**Target Platform:** Zynq-Xcelerate (Xilinx Zynq-7020 SoC)
