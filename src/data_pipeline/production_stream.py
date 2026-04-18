import numpy as np
import os
from src.data_pipeline.generator import generate_wifi_dsss, generate_dji_pulse, generate_jammer

def create_battlefield_stream(n_samples=100):
    """
    Generates a high-complexity, hidden-label production stream.
    Injected with Rayleigh Fading, CFO, and Variable Noise.
    """
    print(f"Creating SkyShield v4.0 Battlefield Stream ({n_samples} hidden samples)...")
    X = []
    GroundTruth = []
    
    for _ in range(n_samples):
        target = np.random.randint(0, 3)
        # Even harsher SNR for production testing (-20dB to 5dB)
        snr = np.random.uniform(-20, 5)
        
        if target == 0: X.append(generate_wifi_dsss(snr))
        elif target == 1: X.append(generate_dji_pulse(snr))
        else: X.append(generate_jammer(snr))
        GroundTruth.append(target)
        
    os.makedirs("data/production", exist_ok=True)
    np.save("data/production/hidden_x.npy", np.array(X))
    np.save("data/production/verification_labels.npy", np.array(GroundTruth))
    print("Battlefield stream ready at data/production/")

if __name__ == "__main__":
    create_battlefield_stream()
