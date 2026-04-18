# High-Capacity RF Signal Classification for Zynq-7020 SoC FPGA

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)

## Overview

This repository implements a high-capacity RF anomaly detection and classification system specifically optimized for deployment on the Xilinx Zynq-7020 SoC FPGA. The system utilizes a Multi-Task Residual-Lite 1D-CNN architecture to classify complex baseband waveforms—including Direct Sequence Spread Spectrum (DSSS), pulsed telemetry, and chaotic phase noise—under non-ideal channel conditions.

The design is optimized for Block RAM (BRAM) efficiency and deterministic sub-millisecond inference latency, making it suitable for real-time electronic defense and signal intelligence applications.

---

## System Architecture

The model utilizes a **Shared Residual Backbone** topology to minimize DSP slice consumption. A single feature extraction pass generates high-dimensional embeddings that are interpreted by three specialized classification heads.

### Technical Specifications
| Parameter | Specification |
| :--- | :--- |
| **Total Parameters** | 340,709 |
| **Input Tensor** | 2 x 512 (I/Q Time-Domain) |
| **Quantization** | INT8 Hardware-Aware |
| **BRAM Footprint** | ~341 KB (57% of Zynq-7020 BRAM) |
| **Inference Latency** | 0.08ms per sample (CPU baseline) |

### Topology Diagram
```text
[Input: 2 x 512 I/Q Tensor]
          |
[Wide Kernel Projection (k=11, 48 channels)]
          |
[Residual Stage 1: 48 filters, stride 1]
          |
[Residual Stage 2: 96 filters, stride 2]
          |
[Residual Stage 3: 96 filters, stride 2]
          |
[Residual Stage 4: 192 filters, stride 2]
          |
[Global Average Pooling] -> [192-dimensional Embedding]
          |_______________________________________________________
          |                       |                              |
[Binary Detection]       [3-Class Identification]      [Entropy Analysis]
(Threat vs Benign)       (WiFi / Drone / Jammer)       (Jamming Verification)
```

---

## Mathematical Foundations

### 1. Waveform Synthesis Models
*   **WiFi (IEEE 802.11b)**: Modeled via 11-chip Barker sequence spreading.
*   **UAV Telemetry (DJI Pulse)**: Simulated as multitone carriers bounded by Gaussian-smoothed rectangular envelopes:
    $$ x(t) = s(t) \cdot e^{j 2 \pi f_c t} \ast g(t) $$
    where $g(t)$ is a Gaussian window used to simulate finite hardware slew rates.
*   **Electronic Warfare (Wiener Jammer)**: Modeled as frequency-sweeping chirps modulated with Wiener-process phase noise (random walk) to simulate chaotic instability:
    $$ \phi_{noise}(t) = \int_0^t \mathcal{N}(0, \sigma^2) d\tau $$

### 2. Signal Propagation & Channel Impairments
Signals are subjected to a complex-baseband impairment model to ensure battlefield robustness:
$$ y(t) = h(t) \cdot x(t) \cdot e^{j 2 \pi \Delta f t} + n(t) $$
*   **Rayleigh Fading ($h(t)$)**: Multipath simulation via complex Gaussian distributions.
*   **Carrier Frequency Offset ($\Delta f$)**: Hardware oscillator drift simulation.
*   **AWGN ($n(t)$)**: Noise floor calibrated for data-driven signal-to-noise ratios (-20dB to 15dB).

---

## Hardware-Aware Training Protocol

To minimize the "reality gap" between high-precision training and fixed-point FPGA deployment, the forward pass incorporates an 8-bit discretization simulator:
$$ x_{fixed} = \frac{\text{clip}(\text{round}(x \cdot 127), -128, 127)}{127.0} $$
This forces the network to learn features that are invariant to quantization noise.

---

## Usage & Deployment

### 1. Installation
```bash
git clone https://github.com/ABHICHIRU/Zynq-Xcelerate.git
cd Zynq-Xcelerate
git checkout production_1d
pip install -r requirements.txt
```

### 2. Live Dashboard Simulation
Run the real-time production dashboard to visualize waveforms and AI decisions:
```bash
python production_dashboard.py
```

### 3. Technical Metrics & Logs
Refer to the `viz_metrics/` directory for Confusion Matrices and `training_history.csv` for convergence data.

---

## References

1.  **O’Shea, T. J., & Hoydis, J. (2017).** "An Introduction to Deep Learning for the Physical Layer." *IEEE Transactions on Cognitive Communications and Networking*.
2.  **Jacob, B., et al. (2018).** "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference." *CVPR*.
3.  **Caruana, R. (1997).** "Multitask Learning." *Machine Learning*.
4.  **Tse, D., & Viswanath, P. (2005).** *Fundamentals of Wireless Communication*. Cambridge University Press.

---
*Disclaimer: This project is intended for defensive research and academic study within the context of FPGA-accelerated signal intelligence.*
