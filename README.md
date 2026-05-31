# Lightweight RF Signal Classification for Zynq-7020 SoC FPGA

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)

## Overview

This repository provides a lightweight, production-grade RF anomaly detection system optimized for the Xilinx Zynq-7020 SoC FPGA. This baseline implementation utilizes an efficient **1D Residual Network (ResNet)** backbone, matching the implementation in `src/core/backbone.py`.

The design is optimized for ultra-low latency edge inference, fitting comfortably within constrained hardware resource limits.

This repository also includes a **high-fidelity Signal Intelligence Dashboard** for real-time visualization of detection engine metrics, threat classification, and model explainability.

## Productionization Roadmap

To ensure this repository is deployable and robust for real-world RF edge inference on Zynq, please address these items:

1. **Code-Documentation Alignment**
    - [ ] Architecture: Confirm README and code both describe a 1D Residual Network (ResNet).
    - [ ] Branch description: Clearly acknowledge this is the quantized, compressed INT8 version.
2. **RF DSP Front-End (Pre-processing)**
    - [ ] Add signal triggering (energy/autocorrelation) to feed correctly-aligned 512-sample I/Q windows.
    - [ ] Implement Carrier Frequency Offset (CFO) correction (e.g., Costas loop) to handle radio drift.
3. **Real SDR Data Integration**
    - [ ] Capture and inject real-world SDR (e.g., HackRF, PlutoSDR) I/Q data into your training pipelines.
    - [ ] Update dataloaders to create a hybrid dataset of synthetic and real recordings.
4. **FPGA Compilation Pipeline**
    - [ ] Pass the trained INT8 PyTorch model through Xilinx Vitis AI or FINN toolchain.
    - [ ] Write a C++/PYNQ wrapper to move SDR data into the FPGA and retrieve classifications.

See inline code comments and project issues for technical guidance.

## System Architecture

The model implements a Shared Backbone architecture (1D ResNet) to maximize hardware efficiency on edge devices.

### Topology Diagram
```text
[Input: 2 x 512 I/Q Tensor]
          |
[1D Convolution + Residual Block (k=7, 32 channels)]
          |
[1D Residual Blocks (k=3, 64/32 channels)]
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

### 2. Running Inference (Headless)
```bash
python verify_inference.py
```

### 3. Interactive Signal Analytics Dashboard
The repository features a professional-grade Streamlit dashboard for visualizing testbench results and threat classifications.

```bash
streamlit run dashboard.py
```

**Key Dashboard Features:**
*   **Signal Monitoring:** Real-time I/Q component and energy envelope visualization.
*   **Detection Engine:** Performance metrics by scenario and energy vs. confidence density.
*   **Threat Classification:** Top-1 vs Top-2 confidence tracking and threat distribution.
*   **Explainability:** Feature correlation heatmaps to justify detection logic.

## References

1.  O’Shea, T. J., & Hoydis, J. (2017). "An Introduction to Deep Learning for the Physical Layer." *IEEE TCCN*.
2.  Caruana, R. (1997). "Multitask Learning." *Machine Learning*.
3.  Jacob, B., et al. (2018). "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference." *CVPR*.
4.  Tse, D., & Viswanath, P. (2005). *Fundamentals of Wireless Communication*.

---
*This branch contains the highly-compressed, quantized (~35KB INT8, ~35,397 parameters) model for deployment. If you are looking for the high-capacity (~341k parameters) reference implementation, please see the `main` or `preproduction` branch.*
