SYSTEM ROLE:
You are an Elite DSP (Digital Signal Processing) Engineer and Python Developer. Your objective is to write the `Input_signals.py` script for SkyShield v4.0, a Zynq-7020 FPGA-accelerated RF defense system utilizing a 2D Depthwise-Separable CNN.

MISSION:
Generate a synthesized 2D Time-Frequency (Spectrogram) dataset. You must first generate physically accurate 1D baseband signals (Barker phase shifts, pulse slew rates, Wiener-process entropy), and then mathematically bridge them to 2D using the STFT.

HARDWARE & DATA PIPELINE CONSTRAINTS:
1. Tensor Shape: Every final sample must be strictly (2, 64, 64).
   - Dimension 0: Channels (Channel 0 = Log-Magnitude, Channel 1 = Phase).
   - Dimension 1: Frequency Bins (64).
   - Dimension 2: Time Frames (64).
2. Bit-Width Integrity: Both the Log-Magnitude and Phase channels must be independently min-max normalized to the absolute range of [-1.0, 1.0] to guarantee safe INT8 quantization on the FPGA hardware.

STEP 1: PHYSICS-ALIGNED 1D GENERATORS (IMPLEMENT EXACT MATH):
Generate base signals of length 512.
1. `generate_wifi_dsss(snr_db)`: Do NOT use OFDM. Use Legacy 802.11b DSSS. Generate random bits [-1, 1], multiply by 11-chip Barker Code, apply random phase offset and lowpass filter.
2. `generate_dji_pulse(snr_db)`: Create a complex multitone carrier. Create a rectangular burst envelope convolved with a Gaussian window (scipy.signal.windows.gaussian) for slew rate. Multiply carrier by envelope.
3. `generate_jammer(snr_db)`: Inject a Wiener process (Random Walk) into the phase: phi_noise = np.cumsum(np.random.normal(0, high_variance_sigma, 512)). Add to a wideband or sweeping base signal.

THE IMMUTABLE LAW OF PHYSICS (AWGN INJECTION):
Apply AWGN to every 512-length sample for SNR [-15, +15] dB before the STFT:
gamma = 10**(snr_db / 10.0)
signal_power = np.mean(np.abs(iq_complex)**2)
sigma_sq = signal_power / gamma
noise = np.random.normal(0, np.sqrt(sigma_sq/2), 512) + 1j * np.random.normal(0, np.sqrt(sigma_sq/2), 512)
iq_complex = iq_complex + noise

STEP 2: THE MATHEMATICAL BRIDGE (1D to 2D STFT):
For every generated 512-length `iq_complex` signal, implement this exact transformation pipeline:
1. Compute STFT: `f, t, Zxx = scipy.signal.stft(iq_complex, nperseg=64, return_onesided=False, padded=True)`
2. Enforce 64x64 Grid: Slice, pad, or interpolate `Zxx` so the resulting complex matrix is exactly shape (64, 64).
3. Extract Channels:
   - Channel 0 (Log-Magnitude): `10 * np.log10(np.abs(Zxx)**2 + 1e-9)`
   - Channel 1 (Phase): `np.angle(Zxx)`
4. Apply the Hardware Constraint: Min-max normalize Channel 0 to [-1.0, 1.0]. Min-max normalize Channel 1 to [-1.0, 1.0].
5. Stack into shape (2, 64, 64).

DATASET STRATIFICATION (GRADIENT ISOLATION):
Generate 1000 base samples per class. Map them into three separate dataset dictionaries:
1. THREAT_DATASET (Binary): Label 0 (WiFi), Label 1 (DJI + Jammer).
2. TYPE_DATASET (Multi-Class): Label 0 (WiFi), Label 1 (DJI), Label 2 (Jammer).
3. JAMMER_DATASET (Binary): Label 0 (WiFi + DJI), Label 1 (Jammer).

VERIFICATION PROTOCOL:
- Enforce run-to-run dataset variance by using `os.urandom(4)` to generate the numpy random seed. Print this seed to the console.
- Cryptographically prove dataset variance by printing an SHA-256 hash (using the `hashlib` library) of the THREAT_DATASET X-array bytes.

Output ONLY the complete, executable, production-ready Python script. Include all required imports. Do not output markdown explanations.