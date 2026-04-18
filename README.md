# Zynq-Xcelerate: High-Capacity 2D RF Anomaly Detection for Zynq-7020 SoC

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)

## Overview

The Zynq-Xcelerate project provides a robust, production-grade pipeline for RF signal classification and anomaly detection, specifically engineered for the Xilinx Zynq-7020 SoC FPGA. This system utilizes advanced 2D Time-Frequency Spectrogram analysis to isolate sophisticated threats—such as frequency-sweeping jammers and UAV telemetry—within complex electromagnetic environments.

The architecture is optimized for Block RAM (BRAM) efficiency and deterministic real-time inference, making it suitable for edge deployment in electronic defense and signal intelligence (SIGINT) applications.

---

## Release Versioning & Evolutionary Roadmap

This project has evolved through multiple architectural iterations to reach production stability.

### v1.0 - v3.0: Baseline 1D-CNN
*   Initial proof-of-concept using raw I/Q time-domain sequences.
*   Implemented multi-task learning for Threat, Type, and Jammer detection.
*   Optimized for minimal DSP usage but lacked robust generalization under multipath fading.

### v4.0 - v5.0: SkyShield Pro (1D)
*   Introduced Residual-Lite stacks to increase depth without exceeding BRAM limits.
*   Integrated hardware-aware training (INT8 simulation).
*   Achieved ~94% accuracy on synthetic distributions.

### v6.0: Echelon Balanced (Current Production)
*   Transition to **2D Time-Frequency Manifolds** via Polyphase Channelizer.
*   Implemented **Global-Context Hybrid 2D ResNet**.
*   Standardized on a 256-dimensional feature embedding.
*   **Result:** Balanced accuracy and latency for Zynq-7020 deployment.

---

## System Architecture

The core engine utilizes a multi-head topology built upon a shared feature extraction backbone.

### Technical Specifications
| Parameter | Specification |
| :--- | :--- |
| **Total Parameters** | ~280,000 |
| **Input Tensor** | 2 x 128 x 128 (Magnitude & Phase) |
| **Quantization** | INT8 Hardware-Aware (Simulated) |
| **BRAM Footprint** | ~450 KB (Post-Quantization Target) |
| **Inference Latency** | 1.17ms (End-to-End on SoC) |

### Mathematical Bridge (1D to 2D)
To interface with real-time 1D IQ streams, the system incorporates a [Polyphase Filter Bank (PFB)](https://en.wikipedia.org/wiki/Polyphase_quadrature_filter) / STFT bridge:
*   **STFT Windowing**: [Hann windowing](https://en.wikipedia.org/wiki/Hann_function) for minimized spectral leakage.
*   **Resolution**: 128x128 grid for high temporal and spectral fidelity.
*   **Normalization**: Robust scaling to [-1, 1] range for hardware compatibility.

---

## Performance Benchmarks

The system has been rigorously validated against a balanced real-time holdout set under variable SNR conditions (-18dB to +18dB). Detailed logs are available in the [BENCHMARK_REPORT_2D.md](BENCHMARK_REPORT_2D.md).

| Metric | Accuracy | Status |
| :--- | :--- | :--- |
| **Threat Detection** | 96.00% | Verified |
| **Type Classification** | 94.50% | Verified |
| **Jammer Isolation** | 95.33% | Verified |
| **False Alarm Rate** | < 11% | Validated |

---

## Hardware-Aware Training Protocol

The pipeline incorporates an 8-bit discretization simulator to ensure that features learned during training are robust to quantization noise encountered during FPGA deployment:
$$ x_{fixed} = \frac{\text{clip}(\text{round}(x \cdot 127), -128, 127)}{127.0} $$

This methodology ensures high fidelity between [PyTorch](https://pytorch.org/) simulation and [Vitis AI](https://www.xilinx.com/products/design-tools/vitis/vitis-ai.html) or [hls4ml](https://fastmachinelearning.org/hls4ml/) deployment.

---

## Usage & Deployment

### 1. Installation
```bash
git clone https://github.com/ABHICHIRU/Zynq-Xcelerate.git
cd Zynq-Xcelerate
git checkout feature/2d-elite-pipeline
pip install -r requirements.txt
```

### 2. End-to-End Production Loop
To run the live production inference simulation (1D Stream -> 2D Bridge -> Inference -> RTL Voting):
```bash
python main.py
```

### 3. Tactical HUD Demo (Web Interface)
A high-impact, military-style drag-and-drop interface for demonstration:
```bash
# 1. Start the backend
python demo_app.py

# 2. Access the HUD
# Open browser at http://localhost:8080
```
*Note: Test samples are available in the `demo_samples/` directory.*

### 4. Verification Suite
Execute the ruthless mixed-signal stress test:
```bash
python end_to_end_mixed_test.py
```

---

## References & Foundational Research

1.  **O’Shea, T. J., & Hoydis, J. (2017).** ["An Introduction to Deep Learning for the Physical Layer."](https://ieeexplore.ieee.org/document/7924307) *IEEE Transactions on Cognitive Communications and Networking*.
2.  **Jacob, B., et al. (2018).** ["Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference."](https://openaccess.thecvf.com/content_cvpr_2018/html/Jacob_Quantization_and_Training_CVPR_2018_paper.html) *CVPR*.
3.  **Zhang, H., et al. (2020).** ["ResNeSt: Split-Attention Networks."](https://arxiv.org/abs/2004.08955) *arXiv:2004.08955* (Foundational for Global-Context Blocks).
4.  **Tse, D., & Viswanath, P. (2005).** [*Fundamentals of Wireless Communication*](https://web.stanford.edu/~dntse/Chapters_PDF/Fundamentals_Wireless_Communication_chapter1.pdf). Cambridge University Press.
5.  **Duarte, M., et al. (2018).** ["Fast inference of deep neural networks in FPGAs for particle physics."](https://arxiv.org/abs/1804.06913) *JINST* (Core principles for [hls4ml](https://fastmachinelearning.org/hls4ml/)).

---
*Disclaimer: This project is intended for defensive research and academic study within the context of FPGA-accelerated signal intelligence.*
