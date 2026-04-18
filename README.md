# SkyShield v4.2: FPGA-Accelerated RF Defense System

SkyShield v4.2 is a production-grade RF anomaly detection and classification system optimized for the **Zynq-7020 SoC FPGA**. It utilizes a Multi-Task Residual-Lite 1D-CNN architecture to detect and classify drone signatures, WiFi signals, and electronic warfare (Jamming) in real-time.

## 🚀 Key Features
- **Data-Driven Intelligence**: Calibrated using real-world I/Q patterns extracted from `logged_data.csv`.
- **Battlefield Physics**: Robust against Rayleigh Fading, Carrier Frequency Offset (CFO), and extreme noise (-20dB SNR).
- **Hardware Optimized**: Residual-Lite backbone designed for INT8 quantization and sub-millisecond inference on edge hardware.
- **RTL Deterministic Voting**: A hardware-style logic gate that combines AI predictions into safe, deterministic system actions.

## 🛠 Project Structure
- `src/core/`: Neural network architecture (Backbone + Heads) and RTL logic.
- `src/data_pipeline/`: Data-driven generators and live stream simulators.
- `models/final_production/`: Trained weights for the Residual-Lite model.
- `viz_metrics/`: Confusion matrices and live inference outcome graphs.

## 📊 Performance Summary
- **Real-Time Accuracy**: 90.0% under battlefield conditions.
- **Decision Consistency**: 96.8% on high-SNR holdout data.
- **Inference Latency**: ~0.04ms per sample (CPU baseline).
- **Threat Leakage**: < 1% (Proving high reliability for defense applications).

## 🏃 How to Run the Pipeline
1. **Analyze Data**: `python analyze_real_data.py` (Extracts patterns from real logs).
2. **Train Model**: `python train_final.py` (Performs data-driven fine-tuning).
3. **Run Dashboard**: `python production_dashboard.py` (Simulates live stream + generates graphs).
4. **Validate**: `python production_validation.py` (Performs a deep production audit).

## 🛡 Verification Protocol
The system includes a `realtime_pipeline_check.py` script that generates a completely randomized, hidden-label stream to verify that the model has learned the underlying RF physics rather than just memorizing the generator logic.
