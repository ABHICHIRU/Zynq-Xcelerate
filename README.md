# Zynq-Xcelerate: High-Capacity 2D RF Anomaly Detection for Zynq-7020 SoC

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![PyTorch 2.0+](https://img.shields.io/badge/PyTorch-2.0+-ee4c2c.svg)](https://pytorch.org/)
[![Hardware: Zynq-7020](https://img.shields.io/badge/Hardware-Zynq--7020-orange.svg)](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html)
[![Branch: production-elite-2d](https://img.shields.io/badge/branch-production--elite--2d-brightgreen.svg)](#)

---

## Abstract

The **Zynq-Xcelerate** project implements a production-grade, multi-task deep learning pipeline for real-time RF signal classification and anomaly detection, engineered for deployment on the [Xilinx Zynq-7020 SoC FPGA](https://www.xilinx.com/products/silicon-devices/soc/zynq-7000.html). The system performs 2D Time-Frequency Spectrogram analysis to isolate sophisticated electromagnetic threats — including frequency-sweeping jammers, FHSS unmanned aerial vehicle (UAV) telemetry, and covert electronic warfare emissions — within dense IEEE 802.11 environments.

The architecture is optimized for Block RAM (BRAM) efficiency and deterministic sub-millisecond inference latency, targeting edge deployment in electronic defense and signal intelligence (SIGINT) applications.

> **Related Branch:** The FPGA synthesis and RTL implementation is maintained on the [`verilog_implementation_main_model`](https://github.com/ABHICHIRU/Zynq-Xcelerate/tree/verilog_implementation_main_model) branch. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the hardware-software co-design overview.

---

## Table of Contents

- [Release Versioning & Evolutionary Roadmap](#release-versioning--evolutionary-roadmap)
- [System Architecture](#system-architecture)
- [Performance Benchmarks](#performance-benchmarks)
- [Hardware-Aware Training Protocol](#hardware-aware-training-protocol)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Usage & Deployment](#usage--deployment)
- [FPGA RTL Integration](#fpga-rtl-integration)
- [References & Foundational Research](#references--foundational-research)

---

## Release Versioning & Evolutionary Roadmap

This project has evolved through multiple architectural iterations to achieve production stability. Each version addressed specific limitations identified through rigorous empirical evaluation.

| Version | Codename | Architecture | Key Advancement | Outcome |
|:--------|:---------|:-------------|:----------------|:--------|
| v1.0–v3.0 | Baseline 1D-CNN | 1D Conv + FC | Multi-task learning (Threat / Type / Jammer) | Limited generalization under multipath fading |
| v4.0–v5.0 | SkyShield Pro | 1D Residual-Lite | Depth scaling within BRAM limits; INT8 QAT | ~94% accuracy on synthetic distributions |
| **v6.0** | **Echelon Balanced** | **2D Global-Context ResNet** | **Time-Frequency manifolds via Polyphase Channelizer** | **96% threat detection; 1.17 ms latency** |

### v6.0 Echelon Balanced (Current Production)

- Transition from raw 1D I/Q sequences to **2D Time-Frequency Spectrogram** representations.
- Implementation of a **Global-Context Hybrid 2D ResNet** backbone with three specialized classification heads.
- Standardized on a 256-dimensional feature embedding for downstream multi-task inference.
- Post-quantization BRAM footprint of ~450 KB, well within Zynq-7020 constraints.

> **Development Note:** An initial 2D evaluation revealed a generalization gap between synthetic training distributions and real-time captured data (documented in [`docs/RUTHLESS_2D_VERIFICATION_REPORT.md`](docs/RUTHLESS_2D_VERIFICATION_REPORT.md)). This was subsequently resolved through domain adaptation and real-world data augmentation using field-captured I/Q recordings (`logs/logged_data.csv`). The final production metrics reported herein reflect the corrected pipeline.

---

## System Architecture

The core inference engine employs a **multi-head topology** built upon a shared feature extraction backbone. A single forward pass through the backbone generates a high-dimensional embedding, which is simultaneously interpreted by three specialized classification heads.

### Technical Specifications

| Parameter | Specification |
|:---|:---|
| **Model Codename** | Echelon v6.0 Balanced |
| **Backbone** | 3-Stage Residual Stack with Global Context (GC) Blocks |
| **Total Parameters** | ~280,000 |
| **Feature Embedding** | 256-dimensional semantic manifold |
| **Input Tensor** | `(2, 128, 128)` — Channel 0: Log-Magnitude (dB), Channel 1: Phase (rad) |
| **Quantization** | INT8 Hardware-Aware (Symmetric/Asymmetric hybrid, simulated) |
| **BRAM Footprint** | ~450 KB (post-quantization target) |
| **Inference Latency** | 1.17 ms (end-to-end on SoC) |
| **Target Platform** | Xilinx Zynq-7020 SoC |

### Multi-Head Decision Engine

```text
[Input: 2 × 128 × 128 Spectrogram (Magnitude + Phase)]
              │
  ┌───────────┴───────────┐
  │  STFT / PFB Bridge    │  ← 1D I/Q Stream (512 samples)
  │  (Hann Window, 128²)  │
  └───────────┬───────────┘
              │
  ┌───────────┴───────────┐
  │  Global-Context       │
  │  Hybrid 2D ResNet     │
  │  (3 Residual Stages)  │
  └───────────┬───────────┘
              │
    256-dim Feature Embedding
     ┌────────┼────────┐
     │        │        │
  ┌──┴──┐ ┌──┴──┐ ┌──┴──┐
  │Threat│ │Type │ │Jammer│
  │Head  │ │Head │ │Head  │
  │(2-cl)│ │(3-cl)│ │(2-cl)│
  └──┬──┘ └──┬──┘ └──┬──┘
     │        │        │
  ┌──┴────────┴────────┴──┐
  │   RTL Voting Logic    │  ← Hardware response codes
  └───────────────────────┘
```

### Mathematical Bridge: 1D → 2D Transformation

To interface with real-time 1D complex I/Q streams, the system incorporates a [Polyphase Filter Bank (PFB)](https://en.wikipedia.org/wiki/Polyphase_quadrature_filter) / Short-Time Fourier Transform (STFT) bridge:

1. **Windowing:** [Hann window](https://en.wikipedia.org/wiki/Hann_function) applied to minimize spectral leakage artifacts.
2. **STFT Computation:** `scipy.signal.stft(iq_complex, nperseg=128, return_onesided=False)`
3. **Resolution:** 128 × 128 grid providing high temporal and spectral fidelity.
4. **Channel Extraction:**
   - Channel 0 (Log-Magnitude): $10 \cdot \log_{10}(|Z_{xx}|^2 + \epsilon)$, where $\epsilon = 10^{-9}$
   - Channel 1 (Phase): $\angle Z_{xx}$
5. **Normalization:** Robust min-max scaling to $[-1, 1]$ for INT8 hardware compatibility.

---

## Performance Benchmarks

The system has been rigorously validated against a balanced real-time holdout set under variable signal-to-noise ratio (SNR) conditions ranging from −18 dB to +18 dB. Full benchmark methodology and raw results are documented in [`docs/BENCHMARK_REPORT_2D.md`](docs/BENCHMARK_REPORT_2D.md).

| Metric | Result | Status |
|:---|:---|:---|
| **Threat Detection Accuracy** | 96.00% | ✅ Verified |
| **Type Classification Accuracy** | 94.50% | ✅ Verified |
| **Jammer Isolation Accuracy** | 95.33% | ✅ Verified |
| **False Alarm Rate (WiFi)** | < 11% | ✅ Validated |
| **Detection Recall (Drone/Jammer)** | > 98% | ✅ Mission Critical |
| **End-to-End Inference Latency** | 1.17 ms | ✅ Real-Time |

### Visualization Gallery

| Visualization | Description |
|:---|:---|
| [`assets/spectrogram_comparison.png`](assets/spectrogram_comparison.png) | 1D-to-2D spectrogram bridge comparison |
| [`assets/viz_2d_samples.png`](assets/viz_2d_samples.png) | Sample 2D spectrograms per signal class |
| [`assets/viz_heads_2d.png`](assets/viz_heads_2d.png) | Multi-head attention activations |
| [`assets/viz_model_threat.png`](assets/viz_model_threat.png) | Threat head confusion matrix |
| [`assets/viz_model_type.png`](assets/viz_model_type.png) | Type head confusion matrix |
| [`assets/viz_model_jammer.png`](assets/viz_model_jammer.png) | Jammer head confusion matrix |
| [`assets/viz_raw_1d_physics.png`](assets/viz_raw_1d_physics.png) | Raw 1D signal physics visualization |
| [`viz_metrics/training_loss_accuracy.png`](viz_metrics/training_loss_accuracy.png) | Training loss and accuracy convergence |

---

## Hardware-Aware Training Protocol

The training pipeline incorporates an 8-bit discretization simulator to ensure that features learned during float32 training are robust to quantization noise encountered during FPGA fixed-point deployment:

$$x_{\text{fixed}} = \frac{\text{clip}\left(\text{round}(x \cdot 127),\; -128,\; 127\right)}{127.0}$$

This Quantization-Aware Training (QAT) methodology ensures high fidelity between [PyTorch](https://pytorch.org/) simulation results and deployment via [Vitis AI](https://www.xilinx.com/products/design-tools/vitis/vitis-ai.html) or [hls4ml](https://fastmachinelearning.org/hls4ml/).

---

## Repository Structure

```
Zynq-Xcelerate/                        (production-elite-2d branch)
│
├── README.md                           # This file
├── main.py                             # Primary entry point — production inference loop
├── demo_app.py                         # FastAPI tactical HUD demo server
├── .gitignore
│
├── docs/                               # Technical documentation
│   ├── ARCHITECTURE.md                 # Cross-reference — ML ↔ RTL integration
│   ├── FINAL_PRODUCTION_REPORT_2D.md   # v6.0 Echelon production report
│   ├── BENCHMARK_REPORT_2D.md          # Quantitative benchmark results
│   ├── RUTHLESS_2D_VERIFICATION_REPORT.md  # Initial 2D verification post-mortem
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
├── src/                                # Core library source code
│   ├── core/                           #   Model architecture definitions
│   │   ├── backbone.py                 #     1D ResNet backbone
│   │   ├── backbone_2d.py              #     2D Global-Context ResNet backbone
│   │   ├── heads.py                    #     1D classification heads
│   │   ├── heads_2d.py                 #     2D classification heads
│   │   └── voting_logic.py             #     RTL voting logic (Python simulation)
│   ├── data_pipeline/                  #   Data loading & generation
│   │   ├── generator.py                #     1D signal generator
│   │   ├── generator_2d.py             #     2D spectrogram generator
│   │   ├── loaders.py                  #     Dataset loaders
│   │   └── production_stream.py        #     Real-time stream interface
│   ├── training/                       #   Training pipeline
│   │   └── train_pipeline.py           #     Main training loop
│   └── utils/                          #   Utility functions
│       ├── channelizer.py              #     Polyphase channelizer / STFT bridge
│       ├── check_data_quality.py       #     Data quality validation
│       ├── physics_check.py            #     1D physics integrity checks
│       └── physics_check_2d.py         #     2D physics integrity checks
│
├── scripts/                            # Standalone executable scripts
│   ├── training/                       #   Model training scripts
│   │   ├── train_2d.py
│   │   ├── train_final.py
│   │   ├── train_final_2d.py
│   │   └── automl_search.py
│   ├── visualization/                  #   Plotting & visualization
│   │   ├── visualize_2d_dataset.py
│   │   ├── visualize_datasets.py
│   │   ├── visualize_heads.py
│   │   ├── visualize_heads_2d.py
│   │   ├── visualize_metrics.py
│   │   └── visualize_raw_1d.py
│   ├── benchmarking/                   #   Performance benchmarking
│   │   ├── benchmark_pipeline.py
│   │   ├── benchmark_pipeline_2d.py
│   │   └── verify_2d_performance.py
│   ├── validation/                     #   End-to-end validation & testing
│   │   ├── end_to_end_mixed_test.py
│   │   ├── production_validation.py
│   │   ├── verify_inference.py
│   │   ├── realtime_pipeline_check.py
│   │   └── analyze_spectral_leakage.py
│   ├── analysis/                       #   Data analysis utilities
│   │   ├── analyze_real_data.py
│   │   └── recover_history.py
│   └── pipeline/                       #   Production pipeline variants
│       ├── production_pipeline_1d.py
│       ├── production_pipeline_2d.py
│       ├── production_dashboard.py
│       ├── Input_signals.py
│       └── generate_master_scan.py
│
├── models/                             # Trained model weights (.pth)
│   ├── production_2d_elite/            #   Current production weights (v6.0)
│   ├── production_2d/                  #   Per-task production models
│   ├── production_2d_int8/             #   INT8 quantized model
│   ├── 2d_bench/                       #   Benchmark variant weights
│   └── ...                             #   Historical model versions
│
├── data/                               # Datasets (.npz, .npy)
│   ├── production_2d/                  #   Production 2D dataset
│   ├── realtime_2d/                    #   Real-time 2D test set
│   ├── production/                     #   1D production verification data
│   └── realtime/                       #   1D real-time test set
│
├── demo_samples/                       # Pre-generated demo signals (.npy)
│   ├── MASTER_BATTLEFIELD_SCAN.npy
│   ├── SCAN_001_WIFI_CLEAR.npy
│   ├── SCAN_002_DRONE_THREAT.npy
│   └── SCAN_003_JAMMER_ACTIVE.npy
│
├── templates/                          # Web UI templates (FastAPI / Jinja2)
│   └── index.html                      #   Tactical HUD interface
│
├── viz_metrics/                        # Training metric visualizations
│   └── training_loss_accuracy.png
│
└── logs/                               # Training logs & captured data
    ├── logged_data.csv                 #   Field-captured I/Q recordings
    ├── training_history_2d.csv         #   Training convergence history
    └── real_world_stats.json           #   Real-world signal statistics
```

---

## Getting Started

### Prerequisites

- Python ≥ 3.12
- PyTorch ≥ 2.0
- NumPy, SciPy, Matplotlib
- FastAPI, Uvicorn (for demo HUD)

### Installation

```bash
git clone https://github.com/ABHICHIRU/Zynq-Xcelerate.git
cd Zynq-Xcelerate
git checkout production-elite-2d
pip install -r requirements.txt
```

---

## Usage & Deployment

### 1. End-to-End Production Inference

Run the live production inference simulation (1D Stream → 2D Bridge → Echelon Inference → RTL Voting):

```bash
python main.py
```

### 2. Tactical HUD Demo (Web Interface)

A military-style drag-and-drop interface for real-time signal analysis demonstration:

```bash
# Start the FastAPI backend
python demo_app.py

# Access the HUD at http://localhost:8080
```

> **Note:** Pre-generated test signals are available in the [`demo_samples/`](demo_samples/) directory. Drag any `.npy` file onto the HUD for instant classification.

### 3. Training

```bash
# Train the 2D Echelon model from scratch
python scripts/training/train_final_2d.py

# Run AutoML architecture search
python scripts/training/automl_search.py
```

### 4. Verification & Benchmarking

```bash
# Full end-to-end mixed-signal stress test
python scripts/validation/end_to_end_mixed_test.py

# Quantitative benchmark against holdout sets
python scripts/benchmarking/benchmark_pipeline_2d.py

# Verify inference correctness
python scripts/validation/verify_inference.py
```

### 5. Visualization

```bash
# Visualize 2D spectrogram samples
python scripts/visualization/visualize_2d_dataset.py

# Render multi-head attention maps
python scripts/visualization/visualize_heads_2d.py
```

---

## FPGA RTL Integration

The FPGA synthesis and Register-Transfer Level (RTL) implementation for the Zynq-7020 SoC is maintained on the **[`verilog_implementation_main_model`](https://github.com/ABHICHIRU/Zynq-Xcelerate/tree/verilog_implementation_main_model)** branch. The two branches are interdependent:

- **This branch (`production-elite-2d`)** — ML model training, data pipeline, inference engine, and validation.
- **RTL branch (`verilog_implementation_main_model`)** — Synthesizable Verilog modules implementing the inference accelerator, voting logic, and SoC integration.

### RTL Module Summary

| Module | Function |
|:---|:---|
| `skyshield_v42_top.v` | Top-level SoC integration wrapper |
| `ml_accelerator_wrapper.v` | ML inference accelerator with AXI interface |
| `threat_detector_rtl.v` | Threat detection head — hardware implementation |
| `type_classifier_rtl.v` | Type classification head — hardware implementation |
| `jammer_detector_rtl.v` | Jammer isolation head — hardware implementation |
| `voting_module_rtl.v` | Multi-head voting and decision logic |
| `tracking_engine.v` | Signal tracking finite state machine |
| `rf_frontend_control.v` | RF front-end SPI/GPIO control interface |
| `power_control.v` | Power management and clock gating unit |

For the complete hardware-software co-design architecture, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## References & Foundational Research

1. **O'Shea, T. J., & Hoydis, J. (2017).** ["An Introduction to Deep Learning for the Physical Layer."](https://ieeexplore.ieee.org/document/7924307) *IEEE Transactions on Cognitive Communications and Networking*, 3(4), 563–575.
2. **Jacob, B., et al. (2018).** ["Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference."](https://openaccess.thecvf.com/content_cvpr_2018/html/Jacob_Quantization_and_Training_CVPR_2018_paper.html) *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*.
3. **Zhang, H., et al. (2020).** ["ResNeSt: Split-Attention Networks."](https://arxiv.org/abs/2004.08955) *arXiv:2004.08955* — Foundational for the Global-Context block design.
4. **Tse, D., & Viswanath, P. (2005).** [*Fundamentals of Wireless Communication*](https://web.stanford.edu/~dntse/Chapters_PDF/Fundamentals_Wireless_Communication_chapter1.pdf). Cambridge University Press.
5. **Duarte, M., et al. (2018).** ["Fast inference of deep neural networks in FPGAs for particle physics."](https://arxiv.org/abs/1804.06913) *Journal of Instrumentation (JINST)* — Core principles for [hls4ml](https://fastmachinelearning.org/hls4ml/).
6. **Caruana, R. (1997).** "Multitask Learning." *Machine Learning*, 28(1), 41–75 — Theoretical basis for the shared-backbone multi-head architecture.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

*This project is intended for defensive research and academic study within the context of FPGA-accelerated signal intelligence. The authors bear no responsibility for misuse of the techniques or implementations described herein.*

---

**Maintained by:** [ABHICHIRU](https://github.com/ABHICHIRU)  
**Target Platform:** Zynq-Xcelerate (Xilinx Zynq-7020 SoC)
