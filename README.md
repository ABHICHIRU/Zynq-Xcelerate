# High-Capacity RF Signal Classification for Zynq-7020 SoC FPGA

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)

## Overview

This repository provides a high-capacity RF anomaly detection and classification system optimized for edge deployment on the Xilinx Zynq-7020 SoC FPGA. The implementation utilizes a Multi-Task Residual-Lite 1D-CNN architecture for real-time classification of complex waveforms, including DSSS, pulsed telemetry, and chaotic phase noise.

The design is engineered to minimize Block RAM (BRAM) footprint and satisfy sub-millisecond inference requirements while maintaining robustness against Rayleigh fading and Carrier Frequency Offset (CFO).

## System Architecture

The model implements a Shared Residual Backbone with specialized classification heads to satisfy multi-task objectives within strict hardware resource bounds.

### Technical Specifications
- **Total Parameters**: 340,709
- **Quantized Footprint**: ~341 KB (INT8 precision)
- **Memory Allocation**: Occupies ~57% of Zynq-7020 on-chip BRAM (~600 KB total capacity).
- **Latency**: 0.08ms per 512-sample window (CPU baseline).

### Topology Diagram
```text
[Input: 2 x 512 I/Q Tensor]
          |
[Wide Kernel Projection (k=11, 48 channels)]
          |
[Residual Stage 1: 48 channels, stride 1]
          |
[Residual Stage 2: 96 channels, stride 2]
          |
[Residual Stage 3: 96 channels, stride 2]
          |
[Residual Stage 4: 192 channels, stride 2]
          |
[Global Average Pooling] -> [192-dimensional Feature Vector]
          |_______________________________________________________
          |                       |                              |
[Threat Head (Binary)]   [Type Head (3-Class)]         [Jammer Head (Binary)]
```

## Mathematical Foundations & Dataset Synthesis

The system utilizes a data-driven synthetic generator calibrated against physical I/Q measurements.

### 1. Signal Models
*   **DSSS (IEEE 802.11b)**: Modeled via 11-chip Barker sequence spreading.
*   **Pulsed RF (UAV Telemetry)**: Complex multitone carrier with Gaussian-smoothed rectangular envelopes.
*   **Chaotic Noise (Jamming)**: Sweeping chirp modulated with Wiener-process phase instability:
    $$ \phi_{noise}(t) = \int_0^t \mathcal{N}(0, \sigma^2) d\tau $$

### 2. Channel Impairments
Signals pass through a simulated propagation channel:
$$ y(t) = h(t) \cdot x(t) \cdot e^{j 2 \pi \Delta f t} + n(t) $$
*   **Rayleigh Fading ($h(t)$)**: Multipath simulation using complex Gaussian distribution.
*   **Carrier Frequency Offset ($\Delta f$)**: Hardware oscillator drift simulation.
*   **AWGN ($n(t)$)**: Calibrated down to -20dB SNR.

## Training Protocol

The pipeline utilizes a hardware-aware protocol incorporating an 8-bit discretization simulator in the forward pass:
$$ x_{fixed} = \frac{\text{clip}(\text{round}(x \cdot 127), -128, 127)}{127.0} $$

## Performance Metrics

*   **Holdout Accuracy**: 96.67%
*   **Real-Time Robustness**: 90.0% (-20dB SNR environments).
*   **Decision Logic**: Deterministic RTL voting for system control.

## Usage

### 1. Environment Setup
```bash
git clone https://github.com/ABHICHIRU/Zynq-Xcelerate.git
cd Zynq-Xcelerate
git checkout production_1d
pip install torch numpy pandas matplotlib scikit-learn scipy
```

### 2. Simulation & Dashboard
```bash
python production_dashboard.py
```

### 3. Model Training
```bash
python train_final.py
```

## References

1.  O’Shea, T. J., & Hoydis, J. (2017). "An Introduction to Deep Learning for the Physical Layer." *IEEE TCCN*.
2.  Caruana, R. (1997). "Multitask Learning." *Machine Learning*.
3.  Jacob, B., et al. (2018). "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference." *CVPR*.
4.  Tse, D., & Viswanath, P. (2005). *Fundamentals of Wireless Communication*.
