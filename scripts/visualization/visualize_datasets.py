import numpy as np
import matplotlib.pyplot as plt
import os

def visualize_samples(dataset_path, num_samples_per_class=1):
    """
    Loads THREAT_DATASET and visualizes samples for WiFi, DJI, and Jammer.
    WiFi: Label 0 (Threat=0)
    DJI: Label 1 (Threat=1) - Samples 1000 to 1999 in threat dataset
    Jammer: Label 1 (Threat=1) - Samples 2000 to 2999 in threat dataset
    """
    if not os.path.exists(dataset_path):
        print(f"Error: {dataset_path} not found.")
        return

    data = np.load(dataset_path)
    X = data['X']
    Y = data['Y']
    
    # We know the stratification:
    # 0-999: WiFi
    # 1000-1999: DJI
    # 2000-2999: Jammer
    
    classes = {
        "WiFi (Barker Code)": (0, 999),
        "DJI (Pulse Edge)": (1000, 1999),
        "Jammer (Wiener Noise)": (2000, 2999)
    }
    
    fig, axes = plt.subplots(len(classes), 1, figsize=(12, 10), constrained_layout=True)
    fig.suptitle('SkyShield v3.0: Generated RF Time-Domain I/Q Samples', fontsize=16)
    
    for idx, (label, (start, end)) in enumerate(classes.items()):
        # Select a random sample within the range
        sample_idx = np.random.randint(start, end + 1)
        sample = X[sample_idx]
        
        ax = axes[idx]
        ax.plot(sample[0], label='I (In-phase)', alpha=0.8)
        ax.plot(sample[1], label='Q (Quadrature)', alpha=0.8)
        ax.set_title(f"Class: {label} (Sample ID: {sample_idx})")
        ax.set_xlabel("Time Samples (512)")
        ax.set_ylabel("Amplitude (Normalized)")
        ax.set_ylim([-1.1, 1.1])
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc='upper right')
        
    plt.savefig('dataset_visualization.png')
    print("Visualization saved to dataset_visualization.png")
    # plt.show() # Not possible in CLI environment, but save is good.

if __name__ == "__main__":
    visualize_samples("data/threat_dataset.npz")
