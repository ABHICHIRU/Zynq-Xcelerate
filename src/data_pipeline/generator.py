import numpy as np
import scipy.signal
import os
import hashlib

def apply_awgn(iq_complex, snr_db):
    gamma = 10**(snr_db / 10.0)
    signal_power = np.mean(np.abs(iq_complex)**2)
    if signal_power == 0: signal_power = 1e-10
    sigma_sq = signal_power / gamma
    noise = (np.random.normal(0, np.sqrt(sigma_sq/2), 512) + 
             1j * np.random.normal(0, np.sqrt(sigma_sq/2), 512))
    return iq_complex + noise

def normalize_iq(iq_complex):
    i_chan = iq_complex.real.astype(np.float32)
    q_chan = iq_complex.imag.astype(np.float32)
    combined = np.stack([i_chan, q_chan])
    c_min, c_max = combined.min(), combined.max()
    if c_max != c_min:
        combined = 2 * (combined - c_min) / (c_max - c_min) - 1.0
    else:
        combined = combined - c_min
    return combined

def generate_wifi_dsss(snr_db):
    barker = np.array([1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1])
    bits = np.random.choice([-1, 1], size=10)
    chips = np.concatenate([bit * barker for bit in bits])
    t_orig = np.linspace(0, 1, len(chips))
    t_new = np.linspace(0, 1, 512)
    iq_base = np.interp(t_new, t_orig, chips) + 0j
    theta = np.random.uniform(0, 2 * np.pi)
    iq_phase = iq_base * np.exp(1j * theta)
    b, a = scipy.signal.butter(4, 0.2)
    iq_filtered = scipy.signal.lfilter(b, a, iq_phase)
    return normalize_iq(apply_awgn(iq_filtered, snr_db))

def generate_dji_pulse(snr_db):
    t = np.linspace(0, 1, 512)
    f1, f2 = np.random.uniform(5, 20), np.random.uniform(30, 50)
    carrier = np.exp(1j * 2 * np.pi * f1 * t) + np.exp(1j * 2 * np.pi * f2 * t)
    envelope = np.zeros(512); envelope[100:400] = 1.0
    window_size = 51
    gaussian = scipy.signal.windows.gaussian(window_size, std=7)
    gaussian /= np.sum(gaussian)
    envelope_smoothed = np.convolve(envelope, gaussian, mode='same')
    return normalize_iq(apply_awgn(carrier * envelope_smoothed, snr_db))

def generate_jammer(snr_db):
    t = np.linspace(0, 1, 512)
    f0, f1 = np.random.uniform(5, 15), np.random.uniform(40, 60)
    chirp = scipy.signal.chirp(t, f0=f0, f1=f1, t1=1, method='linear')
    iq_base = chirp + 1j * np.roll(chirp, 128)
    phi_noise = np.cumsum(np.random.normal(0, 0.5, 512))
    return normalize_iq(apply_awgn(iq_base * np.exp(1j * phi_noise), snr_db))

def save_datasets(output_dir="data"):
    seed = int.from_bytes(os.urandom(4), byteorder='big')
    np.random.seed(seed)
    n_samples = 1000
    
    wifi = np.array([generate_wifi_dsss(np.random.uniform(-15, 15)) for _ in range(n_samples)])
    dji = np.array([generate_dji_pulse(np.random.uniform(-15, 15)) for _ in range(n_samples)])
    jammer = np.array([generate_jammer(np.random.uniform(-15, 15)) for _ in range(n_samples)])
    
    # Stratification as per instruction.md
    # 1. THREAT: 0: WiFi, 1: DJI+Jammer
    threat_x = np.concatenate([wifi, dji, jammer])
    threat_y = np.concatenate([np.zeros(1000), np.ones(2000)])
    np.savez(f"{output_dir}/threat_dataset.npz", X=threat_x, Y=threat_y)
    
    # 2. TYPE: 0: WiFi, 1: DJI, 2: Jammer
    type_y = np.concatenate([np.zeros(1000), np.ones(1000), np.ones(1000)*2])
    np.savez(f"{output_dir}/type_dataset.npz", X=threat_x, Y=type_y)
    
    # 3. JAMMER: 0: WiFi+DJI, 1: Jammer
    jammer_y = np.concatenate([np.zeros(2000), np.ones(1000)])
    np.savez(f"{output_dir}/jammer_dataset.npz", X=threat_x, Y=jammer_y)
    
    print(f"Random Seed: {seed}")
    print(f"SHA-256: {hashlib.sha256(threat_x.tobytes()).hexdigest()}")
    print(f"Datasets saved to {output_dir}/")

if __name__ == "__main__":
    save_datasets()
