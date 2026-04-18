import numpy as np
import scipy.signal
import os
import hashlib

def apply_complex_physics(iq_complex, snr_db):
    """
    Applies Real-World RF Impairments:
    1. AWGN Noise
    2. Rayleigh Fading (Multipath simulation)
    3. Frequency Offset (CFO)
    """
    # 1. Carrier Frequency Offset (CFO) - Phase rotation over time
    t = np.linspace(0, 1, 512)
    cfo = np.random.uniform(-0.05, 0.05)
    iq_complex = iq_complex * np.exp(1j * 2 * np.pi * cfo * t)
    
    # 2. Rayleigh Fading (Simulate signal bouncing off buildings)
    h = (np.random.normal(0, 0.707) + 1j * np.random.normal(0, 0.707))
    iq_complex = iq_complex * np.abs(h)
    
    # 3. AWGN
    gamma = 10**(snr_db / 10.0)
    sig_pwr = np.mean(np.abs(iq_complex)**2)
    if sig_pwr == 0: sig_pwr = 1e-10
    sigma_sq = sig_pwr / gamma
    noise = (np.random.normal(0, np.sqrt(sigma_sq/2), 512) + 
             1j * np.random.normal(0, np.sqrt(sigma_sq/2), 512))
    
    return iq_complex + noise

def normalize_iq(iq_complex):
    combined = np.stack([iq_complex.real, iq_complex.imag]).astype(np.float32)
    c_min, c_max = combined.min(), combined.max()
    if c_max != c_min:
        combined = 2 * (combined - c_min) / (c_max - c_min) - 1.0
    return combined

def generate_wifi_dsss(snr_db):
    barker = np.array([1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1])
    bits = np.random.choice([-1, 1], size=10)
    chips = np.concatenate([bit * barker for bit in bits])
    t_new = np.linspace(0, 1, 512)
    iq_base = np.interp(t_new, np.linspace(0, 1, len(chips)), chips) + 0j
    # Fading and CFO applied
    return normalize_iq(apply_complex_physics(iq_base, snr_db))

def generate_dji_pulse(snr_db):
    t = np.linspace(0, 1, 512)
    carrier = np.exp(1j * 2 * np.pi * np.random.uniform(5, 40) * t)
    envelope = np.zeros(512); envelope[100:400] = 1.0
    gaussian = scipy.signal.windows.gaussian(51, std=np.random.uniform(3, 10))
    envelope_smoothed = np.convolve(envelope, gaussian/np.sum(gaussian), mode='same')
    return normalize_iq(apply_complex_physics(carrier * envelope_smoothed, snr_db))

def generate_jammer(snr_db):
    t = np.linspace(0, 1, 512)
    chirp = scipy.signal.chirp(t, f0=np.random.uniform(5,15), f1=np.random.uniform(40,60), t1=1)
    iq_base = chirp + 1j * np.roll(chirp, 128)
    phi_noise = np.cumsum(np.random.normal(0, 0.8, 512)) # Heavier Wiener noise
    iq_unstable = iq_base * np.exp(1j * phi_noise)
    return normalize_iq(apply_complex_physics(iq_unstable, snr_db))

def save_datasets(output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    n_samples = 2000 # Increased dataset size for complexity
    
    wifi = np.array([generate_wifi_dsss(np.random.uniform(-15, 10)) for _ in range(n_samples)])
    dji = np.array([generate_dji_pulse(np.random.uniform(-15, 10)) for _ in range(n_samples)])
    jammer = np.array([generate_jammer(np.random.uniform(-15, 10)) for _ in range(n_samples)])
    
    threat_x = np.concatenate([wifi, dji, jammer])
    threat_y = np.concatenate([np.zeros(n_samples), np.ones(2*n_samples)])
    np.savez(f"{output_dir}/threat_dataset.npz", X=threat_x, Y=threat_y)
    
    type_y = np.concatenate([np.zeros(n_samples), np.ones(n_samples), np.ones(n_samples)*2])
    np.savez(f"{output_dir}/type_dataset.npz", X=threat_x, Y=type_y)
    
    jammer_y = np.concatenate([np.zeros(2*n_samples), np.ones(n_samples)])
    np.savez(f"{output_dir}/jammer_dataset.npz", X=threat_x, Y=jammer_y)
    print(f"Hardenend Dataset saved to {output_dir}/")

if __name__ == "__main__":
    save_datasets()
