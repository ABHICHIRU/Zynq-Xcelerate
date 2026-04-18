SYSTEM ROLE:
You are an Elite DSP (Digital Signal Processing) Engineer and Python Developer. Your objective is to write the `Input_signals.py` script for SkyShield v3.0, a Zynq-7020 FPGA-accelerated RF defense system. 

MISSION:
Generate a synthesized Time-Domain I/Q dataset that forces three parallel 1D-CNNs to learn mathematically distinct RF features (Barker phase shifts, pulse slew rates, and Wiener-process entropy). You must strictly adhere to the laws of RF physics.

HARDWARE & DATA PIPELINE CONSTRAINTS:
1. Tensor Shape: Every sample must be strictly (2, 512). Dim 0 is I (In-phase), Dim 1 is Q (Quadrature). DataType must be float32.
2. Bit-Width Integrity: Every final sample must be min-max normalized to the absolute range of [-1.0, 1.0] to guarantee safe INT8 quantization on the FPGA hardware.

PHYSICS-ALIGNED GENERATORS (IMPLEMENT EXACT MATH):

1. `generate_wifi_dsss(snr_db)` -> Trains Phase Cross-Correlation:
   - CONSTRAINTS: Do NOT use OFDM. Use Legacy 802.11b DSSS.
   - MATH: Generate random binary data [-1, 1]. Multiply by the standard 11-chip Barker Code: [1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1]. 
   - Apply a random phase offset (e^(j*theta)) and a lowpass filter (e.g., scipy.signal.butter) to simulate Root Raised Cosine bandwidth limitations.

2. `generate_dji_pulse(snr_db)` -> Trains Pulse Edge Detection:
   - CONSTRAINTS: Do NOT generate mathematically impossible infinite-bandwidth square waves.
   - MATH: Create a complex multitone carrier. Create a rectangular burst envelope. You MUST convolve this envelope with a Gaussian window (scipy.signal.windows.gaussian) to simulate realistic RF amplifier Rise/Fall times (slew rate). Multiply the carrier by this smoothed envelope.

3. `generate_jammer(snr_db)` -> Trains Phase Instability & Entropy:
   - CONSTRAINTS: Must simulate a saturated, cheap amplifier pushing wideband noise or sweeping chirps.
   - MATH (STABILITY INJECTION): You MUST inject a Wiener process (Random Walk) into the phase. Calculate phase noise as the cumulative sum of a Gaussian distribution: phi_noise = np.cumsum(np.random.normal(0, high_variance_sigma, 512)). Add this chaotic phase to the base signal.

THE IMMUTABLE LAW OF PHYSICS (AWGN INJECTION):
Do NOT create "zero-noise" signals or pure "thermal noise" standalone classes. You MUST apply Additive White Gaussian Noise to every single generated sample to simulate Free Space Path Loss and receiver Johnson-Nyquist noise.
- For a given SNR in the range [-15, +15] dB, implement exactly this logic:
  gamma = 10**(snr_db / 10.0)
  signal_power = np.mean(np.abs(iq_complex)**2)
  sigma_sq = signal_power / gamma
  noise = np.random.normal(0, np.sqrt(sigma_sq/2), 512) + 1j * np.random.normal(0, np.sqrt(sigma_sq/2), 512)
  return iq_complex + noise

DATASET STRATIFICATION (GRADIENT ISOLATION):
Generate 1000 base samples per class. Map them into three separate dataset dictionaries to ensure the three CNN models do not suffer from gradient conflicts:

1. THREAT_DATASET (Binary):
   - Label 0: WiFi samples.
   - Label 1: DJI + Jammer samples.
2. TYPE_DATASET (Multi-Class):
   - Label 0: WiFi samples.
   - Label 1: DJI samples.
   - Label 2: Jammer samples.
3. JAMMER_DATASET (Binary):
   - Label 0: WiFi + DJI samples.
   - Label 1: Jammer samples.

VERIFICATION PROTOCOL:
- Enforce run-to-run dataset variance by using `os.urandom(4)` to generate the numpy random seed. Print this seed to the console.
- Cryptographically prove dataset variance by printing an SHA-256 hash (using the `hashlib` library) of the THREAT_DATASET X-array bytes.

Output ONLY the complete, executable, production-ready Python script. Include all required imports (numpy, scipy.signal, os, hashlib). Do not output markdown explanations.
 
┌─────────────────────────────────────────────────────────────────────────────┐
│          SKYSHIELD AI v3.0 - FPGA EDGE PIPELINE (TIME-DOMAIN)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ Input: (Batch, 2, 512) - Time-Domain I/Q Samples                            │
│        ↑                                                                    │
│        │ 2 channels (I & Q) × 512 temporal samples                          │
│ Hardware Spec:                                                              │
│  INT8 Normalized [-1.0, 1.0] | No FFT / Zero FPU | Sub-millisecond Latency  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌─────────────────────────────────────────────────────────┐              │
│    │               SHARED BACKBONE 1D-CNN                    │              │
│    │             (Feature Extractor - Shared)                │              │
│    │                                                         │              │
│    │  Conv1D(2→16) → DepthwiseConv1D → Conv1D(16→32) →       │              │
│    │  GlobalAvgPool1D → Flattened Feature Vector             │              │
│    └─────────────────────┬───────────────────────────┘              │
│                          │                                          │
│            ┌────────────┼────────────┐                              │
│            │            │            │                              │
│            ▼            ▼            ▼                              │
│    ┌──────────┐   ┌──────────┐   ┌──────────┐                       │
│    │ HEAD A   │   │ HEAD B   │   │ HEAD C   │                       │
│    │ THREAT   │   │  TYPE    │   │ JAMMER   │                       │
│    │(Binary)  │   │(3-Class) │   │(Binary)  │                       │
│    └────┬─────┘   └────┬─────┘   └────┬─────┘                       │
│         │              │              │                             │
│         ▼              ▼              ▼                             │
│    ┌──────┐       ┌──────┐       ┌──────┐                           │
│    │0/1   │       │0-2   │       │0/1   │                           │
│    │Benign│       │WiFi  │       │Clear │                           │
│    │Threat│       │DJI   │       │Jammer│                           │
│    └──────┘       │Jammer│       └──────┘                           │
│         │         └──────┘            │                             │
│         │              │              │                             │
│         └──────────────┼──────────────┘                             │
│                        │                                            │
│                        ▼                                            │
│    ┌────────────────────────────────────────────┐                   │
│    │      RTL DETERMINISTIC VOTING LOGIC        │                   │
│    │          (Hardware Boolean Gate)           │                   │
│    │                                            │                   │
│    │ Rule 1: If Jammer=1                        │                   │
│    │         → OVERRIDE Type. Alert: JAMMING!   │                   │
│    │                                            │                   │
│    │ Rule 2: If Threat=0                        │                   │
│    │         → RESET. Status: BENIGN / STANDBY  │                   │
│    │                                            │                   │
│    │ Rule 3: If Threat=1 AND Jammer=0           │                   │
│    │         → Trust Type head classification   │                   │
│    └────────────────────────────────────────────┘                   │
│                        │                                            │
│                        ▼                                            │
│    ┌────────────────────────────────────────────┐                   │
│    │               FINAL SYSTEM ACTION          │                   │
│    │  [Action_Code, Class_ID, Jammer_Status]    │                   │
│    └────────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘the