import numpy as np
import scipy.signal
import os
import hashlib
import torch

def generate_wifi_dsss(snr_db):
    """Legacy 802.11b DSSS: 11-chip Barker Code, length 512."""
    barker = np.array([1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1])
    bits = np.random.choice([-1, 1], size=46) # 46 * 11 = 506
    chips = np.concatenate([bit * barker for bit in bits])
    # Pad to 512
    chips = np.pad(chips, (0, 512 - len(chips)), 'constant')
    
    # Random phase offset
    phase_offset = np.random.uniform(0, 2 * np.pi)
    iq_base = chips * np.exp(1j * phase_offset)
    
    # Lowpass filter (Butterworth)
    b, a = scipy.signal.butter(4, 0.3)
    iq_base = scipy.signal.lfilter(b, a, iq_base)
    
    return apply_awgn(iq_base, snr_db)

def generate_dji_pulse(snr_db):
    """DJI-style pulse: Complex multitone carrier with Gaussian-slew envelope."""
    t = np.arange(512)
    # Complex multitone carrier
    freqs = np.random.uniform(5, 40, size=3)
    carrier = np.sum([np.exp(1j * 2 * np.pi * f * t / 512) for f in freqs], axis=0)
    
    # Rectangular burst envelope
    envelope = np.zeros(512)
    start, end = 100, 400
    envelope[start:end] = 1.0
    
    # Gaussian window for slew rate
    gaussian = scipy.signal.windows.gaussian(51, std=np.random.uniform(3, 10))
    envelope_smoothed = np.convolve(envelope, gaussian/np.sum(gaussian), mode='same')
    
    return apply_awgn(carrier * envelope_smoothed, snr_db)

def generate_jammer(snr_db):
    """Jammer: Wiener process (Random Walk) phase noise."""
    t = np.arange(512)
    # Wideband sweep base
    base = scipy.signal.chirp(t, f0=10, f1=100, t1=512, method='linear')
    iq_base = base + 1j * np.roll(base, 128)
    
    # Wiener process phase noise
    high_variance_sigma = 0.5
    phi_noise = np.cumsum(np.random.normal(0, high_variance_sigma, 512))
    
    iq_unstable = iq_base * np.exp(1j * phi_noise)
    
    return apply_awgn(iq_unstable, snr_db)

def apply_awgn(iq_complex, snr_db):
    """The Immutable Law of Physics: AWGN Injection."""
    gamma = 10**(snr_db / 10.0)
    signal_power = np.mean(np.abs(iq_complex)**2)
    if signal_power == 0: signal_power = 1e-10
    sigma_sq = signal_power / gamma
    noise = (np.random.normal(0, np.sqrt(sigma_sq/2), 512) + 
             1j * np.random.normal(0, np.sqrt(sigma_sq/2), 512))
    return iq_complex + noise

from src.utils.channelizer import apply_channelizer_2d

def channelizer_bridge(iq_complex):
    """The Mathematical Bridge: 1D to 2D via Polyphase Channelizer (2, 64, 64)."""
    return apply_channelizer_2d(iq_complex)

def generate_dataset_2d(n_samples_per_class=1000):
    # Enforce variance
    seed = int.from_bytes(os.urandom(4), 'big')
    np.random.seed(seed)
    print(f"Random Seed: {seed}")
    
    classes = ['wifi', 'dji', 'jammer']
    data = {c: [] for c in classes}
    
    for _ in range(n_samples_per_class):
        snr = np.random.uniform(-15, 15)
        data['wifi'].append(channelizer_bridge(generate_wifi_dsss(snr)))
        data['dji'].append(channelizer_bridge(generate_dji_pulse(snr)))
        data['jammer'].append(channelizer_bridge(generate_jammer(snr)))
        
    wifi = np.array(data['wifi'])
    dji = np.array(data['dji'])
    jammer = np.array(data['jammer'])
    
    X = np.concatenate([wifi, dji, jammer])
    
    # THREAT_DATASET (Binary): 0: WiFi, 1: DJI + Jammer
    threat_y = np.concatenate([np.zeros(n_samples_per_class), np.ones(2 * n_samples_per_class)])
    
    # TYPE_DATASET (Multi-Class): 0: WiFi, 1: DJI, 2: Jammer
    type_y = np.concatenate([np.zeros(n_samples_per_class), np.ones(n_samples_per_class), np.ones(n_samples_per_class) * 2])
    
    # JAMMER_DATASET (Binary): 0: WiFi + DJI, 1: Jammer
    jammer_y = np.concatenate([np.zeros(2 * n_samples_per_class), np.ones(n_samples_per_class)])
    
    # Verification
    sha256_hash = hashlib.sha256(X.tobytes()).hexdigest()
    print(f"Dataset SHA-256: {sha256_hash}")
    
    return {
        'X': X,
        'threat_y': threat_y,
        'type_y': type_y,
        'jammer_y': jammer_y
    }

if __name__ == "__main__":
    ds = generate_dataset_2d()
    os.makedirs("data/production_2d", exist_ok=True)
    np.savez("data/production_2d/dataset_2d.npz", **ds)
    print("2D Production Dataset saved.")
