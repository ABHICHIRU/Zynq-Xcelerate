import numpy as np
import scipy.signal
import os
import hashlib
import torch
import json

# Load Real-World Patterns
def load_real_stats():
    if os.path.exists("real_world_stats.json"):
        with open("real_world_stats.json", "r") as f:
            return json.load(f)
    return None

REAL_STATS = load_real_stats()

def apply_ultra_physics(iq_complex, snr_db):
    """Extreme Physics for Ultra-Elite Generalization."""
    t = np.linspace(0, 1, len(iq_complex))
    
    # 1. Dynamic CFO with drift
    cfo = np.random.uniform(-0.15, 0.15)
    drift = np.random.uniform(-0.01, 0.01)
    iq_complex = iq_complex * np.exp(1j * 2 * np.pi * (cfo * t + 0.5 * drift * t**2))
    
    # 2. Rician Fading (Line-of-Sight + Multipath)
    k = 3.0 # Rice factor
    s = np.sqrt(k / (k + 1))
    sigma = np.sqrt(1 / (2 * (k + 1)))
    h = (s + sigma * np.random.normal(0, 1)) + 1j * (sigma * np.random.normal(0, 1))
    iq_complex = iq_complex * h
    
    # 3. Dynamic Noise Floor
    actual_snr = snr_db + np.random.normal(0, 4)
    gamma = 10**(actual_snr / 10.0)
    sig_pwr = np.mean(np.abs(iq_complex)**2)
    if sig_pwr == 0: sig_pwr = 1e-10
    
    sigma_sq = sig_pwr / gamma
    noise = (np.random.normal(0, np.sqrt(sigma_sq/2), len(iq_complex)) + 
             1j * np.random.normal(0, np.sqrt(sigma_sq/2), len(iq_complex)))
    
    return iq_complex + noise

def generate_wifi_dsss(snr_db):
    barker = np.array([1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1])
    bits = np.random.choice([-1, 1], size=46)
    chips = np.concatenate([bit * barker for bit in bits])
    chips = np.pad(chips, (0, 512 - len(chips)), 'constant')
    iq_base = chips * np.exp(1j * np.random.uniform(0, 2*np.pi))
    return apply_ultra_physics(iq_base, snr_db)

def generate_dji_pulse(snr_db):
    t = np.arange(512)
    freqs = np.random.uniform(5, 45, size=4)
    carrier = np.sum([np.exp(1j * 2 * np.pi * f * t / 512) for f in freqs], axis=0)
    envelope = np.zeros(512); start = np.random.randint(50, 150); end = start + 300
    envelope[start:end] = 1.0
    gaussian = scipy.signal.windows.gaussian(51, std=np.random.uniform(2, 12))
    envelope_smoothed = np.convolve(envelope, gaussian/np.sum(gaussian), mode='same')
    return apply_ultra_physics(carrier * envelope_smoothed, snr_db)

def generate_jammer(snr_db):
    t = np.arange(512)
    chirp = scipy.signal.chirp(t, f0=np.random.uniform(5, 20), f1=np.random.uniform(80, 120), t1=512)
    iq_base = chirp + 1j * np.roll(chirp, 128)
    phi_noise = np.cumsum(np.random.normal(0, 1.2, 512))
    iq_unstable = iq_base * np.exp(1j * phi_noise)
    return apply_ultra_physics(iq_unstable, snr_db)

from src.utils.channelizer import apply_channelizer_2d

def generate_dataset_2d_ultra(n_samples_per_class=8000):
    print(f"Generating Massive Ultra Dataset ({n_samples_per_class} per class)...")
    X, Y_t, Y_ty, Y_j = [], [], [], []
    for _ in range(n_samples_per_class):
        snr = np.random.uniform(-15, 15)
        # WiFi
        X.append(apply_channelizer_2d(generate_wifi_dsss(snr)))
        Y_t.append(0); Y_ty.append(0); Y_j.append(0)
        # DJI
        dji = generate_dji_pulse(snr)
        if np.random.rand() > 0.8: dji = dji + generate_jammer(snr-10)*0.3
        X.append(apply_channelizer_2d(dji))
        Y_t.append(1); Y_ty.append(1); Y_j.append(0)
        # Jammer
        X.append(apply_channelizer_2d(generate_jammer(snr)))
        Y_t.append(1); Y_ty.append(2); Y_j.append(1)
    
    X = np.array(X).astype(np.float32)
    return {'X': X, 'threat_y': np.array(Y_t), 'type_y': np.array(Y_ty), 'jammer_y': np.array(Y_j)}

if __name__ == "__main__":
    ds = generate_dataset_2d_ultra()
    os.makedirs("data/production_2d", exist_ok=True)
    np.savez("data/production_2d/dataset_2d.npz", **ds)
