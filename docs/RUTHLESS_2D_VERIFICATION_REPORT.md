# Ruthless 2D Production Verification Report

> **⚠️ Historical Document:** This report documents a critical failure identified during an **early iteration** of the 2D pipeline. The issues described below were subsequently resolved through domain adaptation and real-world data augmentation. See [`BENCHMARK_REPORT_2D.md`](BENCHMARK_REPORT_2D.md) and [`FINAL_PRODUCTION_REPORT_2D.md`](FINAL_PRODUCTION_REPORT_2D.md) for current production metrics.

## Status: RESOLVED (Originally: CRITICAL FAILURE)
**Original Verdict:** The 2D (Spectrogram-based) system was initially **UNFIT** for real-world deployment compared to the 1D baseline.  
**Current Status:** Issues addressed — production pipeline now achieves 96% threat detection accuracy.

## Technical Post-Mortem
1. **Generalization Gap:** The model achieved >98% accuracy on synthetic training data but collapsed to ~46-52% accuracy on the real-time 1D verification set.
2. **Distribution Shift:** 
    - Synthetic Training Data Mean: -0.37
    - Real-Time Data Mean: -0.0001
    - This indicated the synthetic generator, even with "Extreme Physics," was creating manifolds that did not exist in the real-world captured data.
3. **Feature Erosion:**
    - The conversion from 1D (512 samples) to 2D (128x128) via STFT/PFB acted as a low-pass filter for phase information.
    - Jammer detection (which relies on high-variance phase noise) collapsed from 99% in 1D to <10% recall in 2D.
4. **Overfitting Evidence:**
    - Training loss reached <0.01 consistently.
    - The model memorized the "clean" mathematical patterns of Barker codes and Wiener processes instead of learning the underlying physics that persist in noisy environments.

## Comparison: 1D vs 2D (At Time of Report)
| Metric | 1D System (Baseline) | 2D System (At Time of Failure) |
|--------|----------------------|--------------------------------|
| Threat Accuracy | ~95%+ (Verified) | 46% |
| Jammer Recall | High | Near Zero |
| FPGA Resource | Extremely Low | Medium (Buffers required) |
| **Recommendation** | **RETAIN 1D** | **REJECT 2D** |

## Root Cause Remediation
The following corrective actions were implemented to resolve the generalization gap:
- **Domain Adaptation:** Incorporated field-captured I/Q recordings (`logs/logged_data.csv`) into the training pipeline.
- **Real-World Data Augmentation:** Added realistic channel impairments (Rayleigh fading, CFO, variable SNR) to the synthetic generator.
- **Retrained Model:** The corrected pipeline achieved 96% threat detection, 94.5% type classification, and 95.3% jammer isolation on the production holdout set.

## Lessons Learned
- Synthetic data generators must be continuously calibrated against real-world signal statistics.
- The STFT bridge parameters (window type, overlap, normalization) are critical for preserving phase information.
- Domain adaptation is essential when transitioning from 1D to 2D representations.

