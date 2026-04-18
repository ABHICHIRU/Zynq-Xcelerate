# Zynq-Xcelerate: High-Capacity 2D RF Anomaly Detection for Zynq-7020 SoC

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)

## Overview

The Zynq-Xcelerate project provides a robust, production-grade pipeline for RF signal classification and anomaly detection, specifically engineered for the Xilinx Zynq-7020 SoC FPGA. Transitioning from 1D time-domain analysis to a high-fidelity 2D Time-Frequency Spectrogram representation, the system utilizes the **SkyShield v6.0 Echelon** architecture to isolate sophisticated threats—such as frequency-sweeping jammers and UAV telemetry—within complex electromagnetic environments.

The system is optimized for Block RAM (BRAM) efficiency and deterministic real-time inference, making it suitable for edge deployment in electronic defense and signal intelligence applications.

## System Architecture: Echelon v6.0

The core engine utilizes a **Global-Context Hybrid 2D ResNet** topology. This design balances feature extraction capacity with the hardware constraints of the Zynq-7020.

### Technical Specifications
| Parameter | Specification |
| :--- | :--- |
| **Total Parameters** | ~280,000 |
| **Input Tensor** | 2 x 128 x 128 (Magnitude & Phase) |
| **Quantization** | INT8 Hardware-Aware (Simulated) |
| **Memory Footprint** | ~1.8 MB (Float32) / ~450 KB (INT8) |
| **Inference Latency** | 1.17ms per sample (including bridge) |

### Mathematical Bridge (1D to 2D)
To interface with real-time 1D IQ streams, the system incorporates a Polyphase Channelizer/STFT bridge:
*   **Windowing**: Hann windowing for minimized spectral leakage.
*   **Resolution**: 128x128 grid for high temporal and spectral fidelity.
*   **Normalization**: Robust scaling to [-1, 1] range for hardware compatibility.

## Performance Benchmarks

The system has been rigorously validated against a balanced real-time holdout set under variable SNR conditions (-18dB to +18dB).

| Metric | Accuracy | Status |
| :--- | :--- | :--- |
| **Threat Detection** | 96.00% | Verified |
| **Type Classification** | 94.50% | Verified |
| **Jammer Isolation** | 95.33% | Verified |
| **False Alarm Rate** | < 11% | Validated |

## Core Components

*   `src/core/backbone_2d.py`: Global-Context Hybrid 2D ResNet implementation.
*   `src/core/heads_2d.py`: Specialized heads for multi-task classification.
*   `src/utils/channelizer.py`: Mathematical bridge for 1D-to-2D transformation.
*   `production_pipeline_2d.py`: End-to-end inference engine with RTL voting logic.
*   `benchmark_pipeline_2d.py`: Automated benchmarking and evaluation suite.

## Hardware-Aware Training

The pipeline incorporates an 8-bit discretization simulator to ensure that features learned during training are robust to quantization noise encountered during FPGA deployment:
$$ x_{fixed} = \frac{\text{clip}(\text{round}(x \cdot 127), -128, 127)}{127.0} $$

## Usage

### Installation
```bash
git clone https://github.com/ABHICHIRU/Zynq-Xcelerate.git
cd Zynq-Xcelerate
git checkout feature/2d-elite-pipeline
pip install -r requirements.txt
```

### Execution
To run the end-to-end production inference simulation:
```bash
python production_pipeline_2d.py
```

To execute the benchmarking suite:
```bash
python benchmark_pipeline_2d.py
```

## Documentation

Comprehensive technical details and metadata are available in:
*   `FINAL_PRODUCTION_REPORT_2D.md`: Full architectural and performance analysis.
*   `BENCHMARK_REPORT_2D.md`: Detailed accuracy and latency logs.

---
*Disclaimer: This project is intended for defensive research and academic study within the context of FPGA-accelerated signal intelligence.*
