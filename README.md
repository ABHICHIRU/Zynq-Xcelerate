# Lightweight RF Signal Classification for Zynq-7020 SoC FPGA

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)

## Overview

This repository provides a lightweight, production-grade RF anomaly detection system optimized for the Xilinx Zynq-7020 SoC FPGA. This baseline implementation utilize an efficient Depthwise Separable 1D-CNN architecture to perform real-time classification of RF waveforms with minimal power and memory overhead.

The design is optimized for ultra-low latency edge inference, fitting comfortably within the most constrained hardware resource limits.

## System Architecture

The model implements a Shared Backbone architecture to maximize hardware efficiency on edge devices.

### Topology Diagram
```text
[Input: 2 x 512 I/Q Tensor]
          |
[1D Convolution (k=7, 32 channels)]
          |
[Depthwise Separable Convolution (k=3, 64 channels)]
          |
[1D Convolution (k=3, 32 channels)]
          |
[Global Average Pooling] -> [32-dimensional Feature Vector]
          |_______________________________________________________
          |                       |                              |
[Threat Head (Binary)]   [Type Head (3-Class)]         [Jammer Head (Binary)]
```

### Hardware Profile
- **Total Parameters**: 35,397
- **Quantized Footprint**: ~35 KB (INT8 precision)
- **Memory Allocation**: Minimal (< 10% of Zynq-7020 on-chip BRAM).
- **Latency**: < 0.04ms per 512-sample window.

## Mathematical Foundations

Datasets are generated using standard RF engineering principles to simulate real-world propagation environments.

### 1. Waveform Synthesis
*   **WiFi (802.11b DSSS)**: 11-chip Barker Code spreading.
*   **DJI Drone (Pulsed RF)**: Complex multitone carrier with Gaussian envelopes.
*   **Jammer (Chaotic Phase Noise)**: FM chirp carrier with Wiener process instability.

### 2. Signal Propagation Model
Signals are subjected to a complex-baseband channel model:
$$ y(t) = h(t) \cdot x(t) \cdot e^{j 2 \pi \Delta f t} + n(t) $$
Where $h(t)$ represents Rayleigh fading, $\Delta f$ represents Carrier Frequency Offset, and $n(t)$ represents AWGN.

## Usage

### 1. Environment Setup
```bash
git clone https://github.com/ABHICHIRU/Zynq-Xcelerate.git
pip install torch numpy pandas matplotlib scikit-learn scipy
```

### 2. Running Inference
```bash
python verify_inference.py
```

## References

1.  O’Shea, T. J., & Hoydis, J. (2017). "An Introduction to Deep Learning for the Physical Layer." *IEEE TCCN*.
2.  Caruana, R. (1997). "Multitask Learning." *Machine Learning*.
3.  Jacob, B., et al. (2018). "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference." *CVPR*.
4.  Tse, D., & Viswanath, P. (2005). *Fundamentals of Wireless Communication*.

---
*For the high-capacity version (~341k parameters), please see the `production_1d` branch.*
