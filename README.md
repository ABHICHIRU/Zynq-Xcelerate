# High-Capacity RF Signal Intelligence for Zynq-7020 SoC FPGA

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Xilinx Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)

## Overview

This repository provides a high-capacity RF anomaly detection and classification system optimized for edge deployment on the Xilinx Zynq-7020 SoC FPGA. The implementation utilizes a Multi-Task Residual-Lite 1D-CNN architecture to classify complex waveforms (DSSS, pulsed telemetry, and chaotic phase noise) in real-time.

The system is engineered to satisfy sub-millisecond inference requirements while maintaining robustness against Rayleigh fading, Carrier Frequency Offset (CFO), and high-noise environments (-20dB SNR).

## System Architecture

The model implements a Shared Residual Backbone with specialized classification heads to optimize hardware resource utilization (DSP slices and BRAM).

### Technical Specifications
- **Parameter Count**: 340,709
- **Memory Footprint**: ~341 KB (at INT8 precision)
- **BRAM Utilization**: ~57% of Zynq-7020 on-chip BRAM (~600 KB capacity).
- **Latency**: 0.08ms per 512-sample window (CPU baseline).

### Network Topology
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
[Threat Classifier]      [Type Classifier]           [Entropy Detector]
(Binary Logic)           (WiFi / Drone / Jammer)     (Phase Noise Analysis)
```

## Mathematical Foundations & Dataset Synthesis

The dataset is generated via a data-driven synthetic engine calibrated against real-world I/Q patterns.

### 1. Signal Models
*   **WiFi 802.11b (DSSS)**: Modeled using the 11-chip Barker sequence $c = [+1, -1, +1, +1, -1, +1, +1, +1, -1, -1, -1]$.
*   **UAV Telemetry (DJI Pulse)**: Simulated as a complex multitone carrier bounded by a Gaussian-smoothed rectangular envelope to simulate finite hardware slew rates.
*   **EW Jamming (Chaotic Noise)**: Modeled as an FM chirp injected with a Wiener process (random walk) to simulate phase instability:
    $$ \phi_{noise}(t) = \int_0^t \mathcal{N}(0, \sigma^2) d\tau $$

### 2. Channel Propagation Model
To ensure generalization, signals pass through a complex-baseband impairment model:
$$ y(t) = h(t) \cdot x(t) \cdot e^{j 2 \pi \Delta f t} + n(t) $$
*   **Rayleigh Fading ($h(t)$)**: Multipath simulation via complex Gaussian distributions.
*   **Carrier Frequency Offset ($\Delta f$)**: Local oscillator drift simulation.
*   **AWGN ($n(t)$)**: Calibrated down to -20dB SNR.

## Training & Quantization Protocol

The pipeline utilizes a **Hardware-Aware Training** protocol. To minimize the quantization gap, the forward pass incorporates an 8-bit discretization simulator:
$$ x_{fixed} = \frac{\text{clip}(\text{round}(x \cdot 127), -128, 127)}{127.0} $$

## Quick Start

### 1. Installation
```bash
git clone https://github.com/ABHICHIRU/Zynq-Xcelerate.git
cd Zynq-Xcelerate
git checkout production_1d
pip install torch numpy pandas matplotlib scikit-learn scipy
```

### 2. Production Dashboard
Run the real-time simulation and decision engine:
```bash
python production_dashboard.py
```

## References

1.  **O’Shea, T. J., & Hoydis, J. (2017).** "An Introduction to Deep Learning for the Physical Layer." *IEEE Transactions on Cognitive Communications and Networking*.
2.  **Caruana, R. (1997).** "Multitask Learning." *Machine Learning*, 28, 41-75.
3.  **Jacob, B., et al. (2018).** "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference." *CVPR*.
4.  **Tse, D., & Viswanath, P. (2005).** *Fundamentals of Wireless Communication*. Cambridge University Press.
