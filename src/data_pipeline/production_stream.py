import numpy as np
import os
from src.data_pipeline.generator import generate_wifi_dsss, generate_dji_pulse, generate_jammer

def create_hidden_production_stream(n_samples=50):
    """
    Generates a new, randomized RF stream.
    Labels are stored separately to simulate 'Hidden' labels during inference.
    """
    print(f"Generating {n_samples} samples for Hidden Production Stream...")
    X = []
    Labels = [] # 0: WiFi, 1: DJI, 2: Jammer
    
    for _ in range(n_samples):
        target = np.random.randint(0, 3)
        snr = np.random.uniform(-5, 15)
        
        if target == 0:
            X.append(generate_wifi_dsss(snr))
        elif target == 1:
            X.append(generate_dji_pulse(snr))
        else:
            X.append(generate_jammer(snr))
        Labels.append(target)
        
    X = np.array(X)
    Labels = np.array(Labels)
    
    os.makedirs("data/production", exist_ok=True)
    # Save only X for 'Hidden' inference
    np.save("data/production/hidden_x.npy", X)
    # Save labels separately for verification only
    np.save("data/production/verification_labels.npy", Labels)
    print("Production stream saved to data/production/")

if __name__ == "__main__":
    create_hidden_production_stream()
