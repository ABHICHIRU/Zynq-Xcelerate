import numpy as np
import os
from src.data_pipeline.generator_2d import generate_wifi_dsss, generate_dji_pulse, generate_jammer

def generate_master_battlefield_scan():
    print("--- Generating Master Wideband Battlefield Scan ---")
    os.makedirs("demo_samples", exist_ok=True)
    
    # We simulate a wideband capture (e.g., 2048 samples)
    # Different signals occurring sequentially or mixed.
    
    # Base floor noise
    master_signal = (np.random.normal(0, 0.01, 2048) + 1j * np.random.normal(0, 0.01, 2048))
    
    # 1. Inject WiFi at the start (Samples 0-512)
    wifi_complex = generate_wifi_dsss(snr_db=15)
    master_signal[0:512] += wifi_complex
    
    # 2. Inject DJI Drone (Samples 700-1212)
    dji_complex = generate_dji_pulse(snr_db=15)
    master_signal[700:1212] += dji_complex
    
    # 3. Inject Jammer (Samples 1400-1912)
    jammer_complex = generate_jammer(snr_db=12)
    master_signal[1400:1912] += jammer_complex
    
    # Save as a single master capture
    np.save("demo_samples/MASTER_BATTLEFIELD_SCAN.npy", master_signal)
    print("Master scan saved to demo_samples/MASTER_BATTLEFIELD_SCAN.npy")

if __name__ == "__main__":
    generate_master_battlefield_scan()
