import numpy as np
import matplotlib.pyplot as plt
import os

def visualize_samples(dataset_path="data/production_2d/dataset_2d.npz"):
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}. Please run src/data_pipeline/generator_2d.py first.")
        return

    data = np.load(dataset_path)
    X = data['X']
    type_y = data['type_y']
    
    classes = ['WiFi (802.11b DSSS)', 'DJI Pulse', 'Jammer (Wiener Phase)']
    n_classes = len(classes)
    
    fig, axes = plt.subplots(n_classes, 2, figsize=(12, 12))
    plt.subplots_adjust(hspace=0.4, wspace=0.3)
    
    for i in range(n_classes):
        # Find indices for this class
        indices = np.where(type_y == i)[0]
        # Pick a random sample
        idx = np.random.choice(indices)
        sample = X[idx] # (2, 64, 64)
        
        # Channel 0: Log-Magnitude
        im0 = axes[i, 0].imshow(sample[0], aspect='auto', origin='lower', cmap='viridis', vmin=-1, vmax=1)
        axes[i, 0].set_title(f"{classes[i]} - Log-Magnitude")
        axes[i, 0].set_xlabel("Time Frames")
        axes[i, 0].set_ylabel("Frequency Bins")
        fig.colorbar(im0, ax=axes[i, 0])
        
        # Channel 1: Phase
        im1 = axes[i, 1].imshow(sample[1], aspect='auto', origin='lower', cmap='twilight', vmin=-1, vmax=1)
        axes[i, 1].set_title(f"{classes[i]} - Phase")
        axes[i, 1].set_xlabel("Time Frames")
        axes[i, 1].set_ylabel("Frequency Bins")
        fig.colorbar(im1, ax=axes[i, 1])
        
    plt.suptitle("SkyShield v4.0 2D Dataset Visualization\n(Polyphase Channelizer Output)", fontsize=16)
    
    output_file = "viz_2d_samples.png"
    plt.savefig(output_file)
    print(f"Visualization saved to {output_file}")
    plt.show()

if __name__ == "__main__":
    visualize_samples()
