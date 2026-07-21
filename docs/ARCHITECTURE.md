# Zynq-Xcelerate: Hardware-Software Co-Design Architecture

> Cross-reference document linking the ML pipeline (`production-elite-2d`) with the FPGA RTL implementation (`verilog_implementation_main_model`).

---

## Overview

The Zynq-Xcelerate system is a hardware-software co-design targeting the Xilinx Zynq-7020 SoC. The design is split across two interdependent branches:

| Branch | Purpose | Contents |
|:---|:---|:---|
| [`production-elite-2d`](https://github.com/ABHICHIRU/Zynq-Xcelerate/tree/production-elite-2d) | ML model development | Training pipeline, inference engine, data generation, benchmarking, and validation scripts |
| [`verilog_implementation_main_model`](https://github.com/ABHICHIRU/Zynq-Xcelerate/tree/verilog_implementation_main_model) | FPGA RTL synthesis | Synthesizable Verilog modules for the inference accelerator, voting logic, memory subsystem, and SoC integration |

---

## Data Flow: End-to-End Processing Pipeline

```text
┌────────────────────────────────────────────────────────────────────┐
│                     ZYNQ-7020 SoC (PL + PS)                       │
│                                                                    │
│  ┌──────────┐     ┌───────────────┐     ┌───────────────────────┐ │
│  │ RF Front │     │ Input Buffer  │     │ ML Accelerator        │ │
│  │ End      │────▶│ RAM + FIFO    │────▶│ Wrapper               │ │
│  │ Control  │     │               │     │                       │ │
│  │ (.v)     │     │ (.v)          │     │  ┌─────────────────┐  │ │
│  └──────────┘     └───────────────┘     │  │ STFT Bridge     │  │ │
│                                         │  │ (Channelizer)   │  │ │
│                                         │  └────────┬────────┘  │ │
│                                         │           │           │ │
│                                         │  ┌────────▼────────┐  │ │
│                                         │  │ 2D ResNet       │  │ │
│                                         │  │ Backbone        │  │ │
│                                         │  │ (INT8 Weights)  │  │ │
│                                         │  └────────┬────────┘  │ │
│                                         │    ┌──────┼──────┐    │ │
│                                         │    │      │      │    │ │
│                                         │  ┌─▼─┐ ┌──▼─┐ ┌─▼──┐ │ │
│                                         │  │THR│ │TYP │ │JAM │ │ │
│                                         │  │DET│ │CLS │ │DET │ │ │
│                                         │  └─┬─┘ └──┬─┘ └─┬──┘ │ │
│                                         │    └──────┼──────┘    │ │
│                                         └───────────┼───────────┘ │
│                                                     │             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────▼───────────┐│
│  │ Power        │   │ Output       │   │ Voting Module          ││
│  │ Control      │   │ Buffer RAM   │◀──│ (Multi-Head Decision)  ││
│  │ (.v)         │   │ (.v)         │   │ (.v)                   ││
│  └──────────────┘   └──────┬───────┘   └────────────────────────┘│
│                            │                                      │
│                   ┌────────▼────────┐                             │
│                   │ Output          │                             │
│                   │ Aggregator      │                             │
│                   │ (.v)            │                             │
│                   └────────┬────────┘                             │
│                            │                                      │
│                   ┌────────▼────────┐                             │
│                   │ Tracking        │                             │
│                   │ Engine          │                             │
│                   │ (.v)            │                             │
│                   └────────┬────────┘                             │
│                            │                                      │
│                        Response Codes                             │
└────────────────────────────────────────────────────────────────────┘
```

---

## RTL Module Hierarchy

The Verilog modules on the `verilog_implementation_main_model` branch are organized into the following functional groups:

### Top-Level Integration

| Module | File | Description |
|:---|:---|:---|
| SkyShield v4.2 Top | `rtl/top/skyshield_v42_top.v` | Top-level wrapper for the complete SoC — instantiates all submodules, AXI interconnect, and clock management |
| SkyShield AI v3 Top | `rtl/top/top_skyshield_ai_v3.v` | Alternative top-level with full AI subsystem integration |
| SkyShield AI v3 (Simplified) | `rtl/top/top_skyshield_ai_v3_simplified.v` | Reduced-resource variant for constrained deployments |

### Inference Core

| Module | File | Description |
|:---|:---|:---|
| ML Accelerator Wrapper | `rtl/core/ml_accelerator_wrapper.v` | AXI-wrapped inference accelerator; manages weight loading and forward-pass scheduling |
| Threat Detector | `rtl/core/threat_detector_rtl.v` | Binary classification head: Clear vs. Threat |
| Type Classifier | `rtl/core/type_classifier_rtl.v` | Multi-class head: WiFi / DJI Drone / Jammer |
| Jammer Detector | `rtl/core/jammer_detector_rtl.v` | Binary head for high-entropy jammer isolation |
| Voting Module | `rtl/core/voting_module_rtl.v` | Combines head outputs into hardware response codes |

### Memory Subsystem

| Module | File | Description |
|:---|:---|:---|
| Input Buffer RAM | `rtl/memory/input_buffer_ram.v` | Dual-port BRAM for I/Q sample buffering |
| Output Buffer RAM | `rtl/memory/output_buffer_ram.v` | Classification result storage |
| Data Input FIFO | `rtl/memory/data_input_fifo.v` | Streaming FIFO for continuous I/Q ingestion |

### Peripherals & Control

| Module | File | Description |
|:---|:---|:---|
| Control Registers | `rtl/peripherals/control_registers.v` | AXI-Lite register file for PS↔PL configuration |
| RF Frontend Control | `rtl/peripherals/rf_frontend_control.v` | SPI/GPIO interface for RF tuner and ADC control |
| Output Aggregator | `rtl/peripherals/output_aggregator.v` | Collects and formats classification outputs |
| Power Control | `rtl/peripherals/power_control.v` | Clock gating and power domain management |
| Tracking Engine | `rtl/peripherals/tracking_engine.v` | Signal tracking FSM for persistent threat monitoring |

---

## Mapping: Python Simulation ↔ Verilog RTL

| Python Module (this branch) | Verilog RTL Module (verilog branch) | Function |
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

The INT8 quantized model (`models/production_2d_int8/zynq_multi_head_int8.pth`) is generated on this branch and consumed by the RTL branch for weight initialization. The quantization formula used is:

$$x_{\text{fixed}} = \frac{\text{clip}\left(\text{round}(x \cdot 127),\; -128,\; 127\right)}{127.0}$$

Weight export to `.coe` (Xilinx coefficient) format or C header arrays for BRAM initialization should be performed as part of the deployment flow.

---

## Development Workflow

1. **ML Development** — Work on `production-elite-2d`. Train, validate, and export INT8 models.
2. **RTL Development** — Work on `verilog_implementation_main_model`. Implement and simulate Verilog modules.
3. **Integration** — Export quantized weights from the ML branch → import into RTL testbenches on the Verilog branch.
4. **Verification** — Run Python simulation (`scripts/validation/`) to generate golden reference outputs. Compare against RTL simulation results.
