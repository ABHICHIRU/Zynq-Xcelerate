import numpy as np
from src.utils.physics_check import check_barker_dsss, check_pulse_slew_rate, check_wiener_entropy
import os

def run_quality_check():
    data_path = "data/threat_dataset.npz"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    data = np.load(data_path)
    X = data['X']
    
    wifi_sample = X[0]
    dji_sample = X[1000]
    jammer_sample = X[2000]
    
    print("--- RF Physics Validation ---")
    
    # Barker Check
    barker_ok = check_barker_dsss(wifi_sample)
    print(f"WiFi Barker Correlation: {'PASS' if barker_ok else 'FAIL'}")
    
    # Slew Rate Check
    slew_ok = check_pulse_slew_rate(dji_sample)
    print(f"DJI Pulse Slew Rate: {'PASS' if slew_ok else 'FAIL'}")
    
    # Wiener Entropy Check
    entropy_ok = check_wiener_entropy(jammer_sample)
    print(f"Jammer Wiener Entropy: {'PASS' if entropy_ok else 'FAIL'}")
    
    # Normalization Check
    norm_ok = (X.min() >= -1.0001 and X.max() <= 1.0001)
    print(f"Dataset Normalization [-1, 1]: {'PASS' if norm_ok else 'FAIL'}")

if __name__ == "__main__":
    run_quality_check()
