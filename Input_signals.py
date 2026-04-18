import numpy as np
import scipy.signal
import os
import hashlib


# -------------------------------------------------------------
# 1D PHYSICS GENERATORS
# -------------------------------------------------------------
def generate_wifi_dsss(snr_db, length=512):
    # 11-chip Barker Code
    barker = np.array([1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1], dtype=np.complex128)
    symbols = np.random.choice([-1, 1], size=length // 11 + 1)
    base_signal = np.kron(symbols, barker)[:length]
    return apply_awgn(base_signal, snr_db)


def generate_dji_pulse(snr_db, length=512):
    t = np.arange(length)
    f_c = np.random.uniform(0.1, 0.4)
    multitone = np.exp(1j * 2 * np.pi * f_c * t) + np.exp(
        1j * 2 * np.pi * (f_c + 0.05) * t
    )

    # Slew rate constrained rectangular envelope
    env = np.zeros(length)
    start, end = np.random.randint(50, 150), np.random.randint(350, 450)
    env[start:end] = 1
    window = scipy.signal.windows.gaussian(51, std=7)
    env = np.convolve(env, window, mode="same") / np.max(window)

    base_signal = multitone * env
    return apply_awgn(base_signal, snr_db)


def generate_jammer(snr_db, length=512):
    t = np.arange(length)
    # Wideband chirp
    f0, f1 = np.random.uniform(0.05, 0.15), np.random.uniform(0.35, 0.45)
    chirp = scipy.signal.chirp(t, f0=f0, t1=length, f1=f1)

    # Wiener Process Phase Noise
    high_variance_sigma = np.random.uniform(0.5, 1.5)
    phi_noise = np.cumsum(np.random.normal(0, high_variance_sigma, length))

    base_signal = chirp * np.exp(1j * phi_noise)
    return apply_awgn(base_signal, snr_db)


# -------------------------------------------------------------
# AWGN INJECTION (THE IMMUTABLE LAW OF PHYSICS)
# -------------------------------------------------------------
def apply_awgn(iq_complex, snr_db):
    sigma_sq = (np.mean(np.abs(iq_complex) ** 2)) / (10 ** (snr_db / 10.0))
    noise = np.random.normal(
        0, np.sqrt(sigma_sq / 2), len(iq_complex)
    ) + 1j * np.random.normal(0, np.sqrt(sigma_sq / 2), len(iq_complex))
    return iq_complex + noise


# -------------------------------------------------------------
# THE MATHEMATICAL BRIDGE (1D -> 2D STFT)
# -------------------------------------------------------------
def process_to_2d(iq_complex):
    # 1. Compute STFT
    f, t, Zxx = scipy.signal.stft(
        iq_complex, nperseg=64, noverlap=56, return_onesided=False
    )

    # 2. Slice/Pad to exactly (64, 64)
    Zxx = Zxx[:64, :64]
    if Zxx.shape[1] < 64:
        pad_width = ((0, 0), (0, 64 - Zxx.shape[1]))
        Zxx = np.pad(Zxx, pad_width, mode="constant")

    # 3. Extract Channels
    ch0_log_mag = 10 * np.log10(np.abs(Zxx) ** 2 + 1e-9)
    ch1_phase = np.angle(Zxx)

    # 4. Apply Hardware Constraint: Min-Max Norm to [-1.0, 1.0]
    def min_max_norm(ch):
        ch_min, ch_max = np.min(ch), np.max(ch)
        if ch_max > ch_min:
            return 2.0 * ((ch - ch_min) / (ch_max - ch_min)) - 1.0
        return ch

    ch0_norm = min_max_norm(ch0_log_mag)
    ch1_norm = min_max_norm(ch1_phase)

    # 5. Stack into (2, 64, 64)
    return np.stack([ch0_norm, ch1_norm], axis=0)


# -------------------------------------------------------------
# DATASET STRATIFICATION & GENERATION
# -------------------------------------------------------------
def generate_datasets():
    # Crypto Seed Verification
    seed_bytes = os.urandom(4)
    seed_int = int.from_bytes(seed_bytes, byteorder="little")
    np.random.seed(seed_int)
    print(f"VERIFICATION SEED: {seed_int}")

    wifi_samples, dji_samples, jammer_samples = [], [], []

    print("Generating 1000 samples per class...")
    for _ in range(1000):
        snr = np.random.uniform(-15, 15)
        wifi_samples.append(process_to_2d(generate_wifi_dsss(snr)))
        dji_samples.append(process_to_2d(generate_dji_pulse(snr)))
        jammer_samples.append(process_to_2d(generate_jammer(snr)))

    wifi = np.array(wifi_samples, dtype=np.float32)
    dji = np.array(dji_samples, dtype=np.float32)
    jammer = np.array(jammer_samples, dtype=np.float32)

    # 1. THREAT_DATASET (1000 WiFi[0], 500 DJI[1] + 500 Jammer[1])
    threat_X = np.concatenate([wifi, dji[:500], jammer[:500]])
    threat_Y = np.concatenate([np.zeros(1000), np.ones(1000)])
    np.savez_compressed("data/threat_dataset_2d.npz", X=threat_X, Y=threat_Y)

    # SHA-256 Verification Protocol
    sha256 = hashlib.sha256(threat_X.tobytes()).hexdigest()
    print(f"THREAT_DATASET X-Array Hash (SHA-256): {sha256}")

    # 2. TYPE_DATASET (1000 WiFi[0], 1000 DJI[1], 1000 Jammer[2])
    type_X = np.concatenate([wifi, dji, jammer])
    type_Y = np.concatenate([np.zeros(1000), np.ones(1000), np.full(1000, 2)])
    np.savez_compressed("data/type_dataset_2d.npz", X=type_X, Y=type_Y)

    # 3. JAMMER_DATASET (500 WiFi[0] + 500 DJI[0], 1000 Jammer[1])
    jammer_X = np.concatenate([wifi[:500], dji[:500], jammer])
    jammer_Y = np.concatenate([np.zeros(1000), np.ones(1000)])
    np.savez_compressed("data/jammer_dataset_2d.npz", X=jammer_X, Y=jammer_Y)

    print("Generation complete. 2D Pipeline Base Established.")


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    generate_datasets()
