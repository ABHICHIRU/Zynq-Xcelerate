# SkyShield v4.2: FPGA-Accelerated RF Signal Intelligence (Baseline)

SkyShield v4.2 is a production-grade RF anomaly detection and classification system optimized for the Xilinx Zynq-7020 SoC FPGA. The system utilizes a multi-task 1D-CNN architecture to perform real-time classification of RF waveforms.

## 1. System Architecture

The model implements a Shared Backbone architecture to minimize DSP slice utilization on the FPGA. 

### 1.1 Model Topology
```
[Input: 2 x 512 I/Q Tensor]
          |
[1D Convolution (k=7, 32 filters)]
          |
[Depthwise Separable Convolution (k=3, 64 filters)]
          |
[1D Convolution (k=3, 32 filters)]
          |
[Global Average Pooling] -> [32-dim Feature Vector]
          |___________________________________________________
          |                    |                              |
[Threat Head (Binary)] [Type Head (3-Class)] [Jammer Head (Binary)]
```

### 1.2 Hardware Constraints
- **Parameters**: 35,397
- **Memory Footprint**: ~140 KB (Float32) / ~35 KB (INT8)
- **BRAM Utilization**: Minimal (< 10% of Zynq-7020 on-chip memory).
- **Latency**: < 0.04ms per sample.

## 2. RF Dataset Synthesis & Mathematical Foundation

Datasets are generated using data-driven physics calibrated against real-world I/Q patterns.

### 2.1 Signal Generation Models
- **WiFi (802.11b DSSS)**: Modeled using 11-chip Barker Code spreading.
- **DJI Drone (Pulsed RF)**: Complex multitone carrier with Gaussian-windowed envelopes.
- **EW Jammer (Chaotic Noise)**: Sweeping chirp carrier with Wiener-process phase noise.

### 2.2 Mathematical Impairments
The following RF impairments are injected mathematically to ensure robustness:
1. **Rayleigh Fading**: Multipath simulation using complex Gaussian distributions.
2. **Carrier Frequency Offset (CFO)**: Phase rotation defined as $\exp(j 2 \pi \Delta f t)$.
3. **AWGN**: Noise floor calibrated for data-driven signal-to-noise ratios.

## 3. Operational Pipeline
1. **Ingestion**: 512-sample I/Q windowing.
2. **Preprocessing**: Normalized for INT8 hardware range.
3. **Inference**: Multi-task classification via Shared Backbone.
4. **Decision**: RTL-deterministic voting logic for system action.
