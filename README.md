# SkyShield: FPGA-Accelerated RF Signal Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)

## Overview

SkyShield v5.0 Pro is an open-source, production-grade Radio Frequency (RF) anomaly detection and classification system. Designed specifically for edge deployment on the **Xilinx Zynq-7020 SoC FPGA**, the system leverages a highly optimized Multi-Task Residual-Lite 1D-CNN. It is capable of real-time classification of benign communications (e.g., IEEE 802.11b DSSS), unauthorized UAV intrusions (e.g., DJI pulsed telemetry), and Electronic Warfare (EW) jamming attacks.

The architecture prioritizes minimal Block RAM (BRAM) utilization and sub-millisecond inference latency while maintaining high robustness against complex battlefield impairments such as Rayleigh fading and Carrier Frequency Offset (CFO).

## System Architecture

To satisfy strict hardware constraints, the model utilizes a **Shared Residual Backbone** coupled with specialized classification heads, adhering to Multi-Task Learning (MTL) paradigms.

### Hardware Constraints & BRAM Optimization
- **Total Parameters**: 340,709
- **Quantized Footprint**: ~341 KB (INT8 precision)
- **Zynq-7020 Fit**: Consumes ~57% of available on-chip BRAM (~600 KB total), leaving ample space for the RTL data channelizer and I/Q ingestion buffers.
- **Latency Target**: Sub-millisecond execution per 512-sample window.

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
(Detection)              (WiFi / Drone / Jammer)       (Entropy Analysis)
```

## Mathematical Foundations & Dataset Synthesis

Given the scarcity of annotated, adversarial RF datasets, SkyShield utilizes a data-driven synthetic generator calibrated against real-world I/Q logs (`logged_data.csv`).

### 1. Signal Models
*   **Benign DSSS (WiFi 802.11b)**: Modeled using the standard 11-chip Barker sequence $c = [+1, -1, +1, +1, -1, +1, +1, +1, -1, -1, -1]$.
*   **UAV Telemetry (DJI Pulse)**: Simulated as a complex multitone carrier bounded by a Gaussian-smoothed rectangular envelope to replicate finite hardware slew rates.
*   **EW Jamming (Wiener Phase Noise)**: Modeled as a sweeping Frequency Modulated (FM) chirp injected with a Wiener process (random walk) to simulate high-entropy phase instability:
    $$ \phi_{noise}(t) = \int_0^t \mathcal{N}(0, \sigma^2) d\tau $$

### 2. Channel Impairments (Battlefield Hardening)
To ensure robust generalization, the generated waveforms $x(t)$ pass through a simulated propagation channel to produce the received signal $y(t)$:
$$ y(t) = h(t) \cdot x(t) \cdot e^{j 2 \pi \Delta f t} + n(t) $$
*   **Rayleigh Fading ($h(t)$)**: Simulates multipath propagation using a complex Gaussian distribution.
*   **Carrier Frequency Offset ($\Delta f$)**: Simulates hardware oscillator drift.
*   **AWGN ($n(t)$)**: Calibrated down to -20dB SNR environments.

## Training Protocol

The system utilizes a **Hardware-Aware Training** pipeline. To minimize the reality gap between floating-point training and INT8 FPGA deployment, the forward pass incorporates an 8-bit discretization simulator:
$$ x_{fixed} = \frac{\text{clip}(\text{round}(x \cdot 127), -128, 127)}{127.0} $$
This ensures the optimizer adapts to quantization noise prior to exporting the `.pth` weights for hardware synthesis.

## Performance Metrics

*   **Peak Validation Accuracy**: 96.67% (on static holdout datasets).
*   **Real-Time Robustness**: 90.0% accuracy on live, randomized streams subjected to extreme noise (-20dB SNR) and multipath fading.
*   **RTL Voting Consistency**: 100% logical mapping from network logits to deterministic system actions (STANDBY, ALERT_DRONE, ALERT_JAMMING).

## Usage & Deployment

### 1. Environment Setup
```bash
git clone https://github.com/ABHICHIRU/Zynq-Xcelerate.git
cd Zynq-Xcelerate
git checkout production_1d
pip install torch numpy pandas matplotlib scikit-learn scipy
```

### 2. Live Production Dashboard
To simulate the FPGA data ingestion and view real-time inference across the three heads:
```bash
python production_dashboard.py
```
This script loads the pre-trained weights from `models/final_production/`, processes a hidden I/Q stream, and applies the RTL voting logic. Output graphs are saved to `viz_metrics/live_inference/`.

### 3. Retraining the Network
```bash
python train_final.py
```
Executes the hardware-aware training loop, utilizing data augmentation (time-rolling and jitter) and L2 regularization to prevent overfitting.

## References

The methodologies implemented in SkyShield are heavily inspired by foundational research in RF machine learning and hardware-software co-design:

1.  **Deep Learning for RF**: O’Shea, T. J., & Hoydis, J. (2017). "An Introduction to Deep Learning for the Physical Layer." *IEEE Transactions on Cognitive Communications and Networking*.
2.  **Multi-Task Learning**: Caruana, R. (1997). "Multitask Learning." *Machine Learning*, 28, 41-75.
3.  **FPGA Quantization**: Jacob, B., et al. (2018). "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference." *CVPR*.
4.  **Wireless Channel Modeling**: Tse, D., & Viswanath, P. (2005). *Fundamentals of Wireless Communication*. Cambridge University Press.

---
*Disclaimer: SkyShield is designed for academic, defensive, and research purposes. Ensure compliance with local RF regulations when deploying active sensing hardware.*
