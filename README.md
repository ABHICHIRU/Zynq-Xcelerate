# SkyShield v5.0 Pro: FPGA-Accelerated RF Signal Intelligence

SkyShield v5.0 Pro is a high-capacity RF anomaly detection and classification system optimized for the Xilinx Zynq-7020 SoC FPGA. The system utilizes a multi-task Residual-Lite 1D-CNN architecture to perform real-time classification of DSSS, Pulsed, and Chaotic waveforms.

## 1. System Architecture

The model implements a Shared Backbone architecture to minimize DSP slice utilization on the FPGA. By executing a single feature extraction pass for three specialized classification heads, the system achieves sub-millisecond inference latency.

### 1.1 Model Topology
```
[Input: 2 x 512 I/Q Tensor]
          |
[Wide Kernel Projection (k=11, 48 filters)]
          |
[Residual Stage 1: 48 filters, stride 1]
          |
[Residual Stage 2: 96 filters, stride 2]
          |
[Residual Stage 3: 96 filters, stride 2]
          |
[Residual Stage 4: 192 filters, stride 2]
          |
[Global Average Pooling] -> [192-dim Feature Vector]
          |___________________________________________________
          |                    |                              |
[Threat Head (Binary)] [Type Head (3-Class)] [Jammer Head (Binary)]
```

### 1.2 Hardware Constraints & BRAM Optimization
- **Parameters**: 340,709
- **Memory Footprint**: ~341 KB (INT8 Quantized)
- **BRAM Utilization**: ~57% of Zynq-7020 on-chip memory.
- **Latency**: 0.08ms per sample (CPU baseline).

## 2. RF Dataset Synthesis & Mathematical Foundation

Datasets are generated using data-driven physics calibrated against real-world I/Q patterns from `logged_data.csv`.

### 2.1 Signal Generation Models
- **WiFi (802.11b DSSS)**: Modeled using 11-chip Barker Code spreading.
- **DJI Drone (Pulsed RF)**: Complex multitone carrier with Gaussian-windowed rectangular envelopes to simulate finite slew rates.
- **EW Jammer (Chaotic Noise)**: Sweeping chirp carrier modulated with Wiener-process phase noise.

### 2.2 Mathematical Impairments (Battlefield Conditions)
To ensure generalization, the following RF impairments are injected mathematically:
1. **Rayleigh Fading**: $y(t) = h(t) \cdot x(t) + n(t)$, where $h(t)$ follows a complex Gaussian distribution simulating multipath.
2. **Carrier Frequency Offset (CFO)**: Phase rotation defined as $\exp(j 2 \pi \Delta f t)$.
3. **AWGN**: Noise floor calibrated to -20dB SNR.

## 3. Training & Validation

The system utilizes a **Hardware-Aware Training** protocol. 

### 3.1 INT8 Discretization Simulation
The training pipeline includes a fixed-point simulator that discretizes I/Q samples to 8-bit integers during the forward pass:
$$x_{fixed} = \text{clip}(\text{round}(x \cdot 127), -128, 127)$$
This ensures the model is robust to quantization noise before deployment to FPGA fabric.

### 3.2 Metrics
Validation accuracy reached **96.67%** using a Cosine Annealing learning rate schedule. Detailed loss and accuracy plots are available in `viz_metrics/training_loss_accuracy.png`.

## 4. Operational Pipeline
1. **Ingestion**: 512-sample I/Q windowing.
2. **Preprocessing**: 8-bit normalization.
3. **Inference**: Multi-task classification via Residual Backbone.
4. **Decision**: RTL-deterministic voting logic for system action.
