# Final Production 2D Benchmark Report

**Model:** Echelon v6.0 Balanced (Global-Context Hybrid 2D ResNet)  
**Branch:** `production-elite-2d`  
**Date:** April 2026  
**Platform:** Xilinx Zynq-7020 SoC (target)  

---

## Methodology

- **Holdout Set:** Balanced real-time 1D I/Q signals bridged to 2D via STFT (128 × 128 spectrograms).
- **SNR Range:** −18 dB to +18 dB, uniformly sampled.
- **Signal Classes:** WiFi (IEEE 802.11b DSSS), DJI UAV Telemetry, Wiener-Phase Jammer.
- **Quantization:** INT8 Hardware-Aware Simulation applied during inference.
- **Evaluation Protocol:** Single forward pass per sample; no test-time augmentation.

---

## Results

| Task | Accuracy | Precision | Recall |
|:---|:---|:---|:---|
| Threat Detection (Binary) | **0.9600** | — | — |
| Type Classification (3-Class) | **0.9450** | — | — |
| Jammer Isolation (Binary) | **0.9533** | — | — |

**End-to-End Inference Latency:** 1.1754 ms/sample

---

## Notes

- These results supersede the earlier verification reported in [`RUTHLESS_2D_VERIFICATION_REPORT.md`](RUTHLESS_2D_VERIFICATION_REPORT.md), which documented a generalization gap in an earlier iteration of the 2D pipeline.
- The performance improvement was achieved through domain adaptation using field-captured I/Q data and augmented training with realistic channel impairments.
- Confusion matrices for each head are available in [`../assets/`](../assets/).
