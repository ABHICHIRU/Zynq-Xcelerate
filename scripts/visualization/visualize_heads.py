import numpy as np
import matplotlib.pyplot as plt
import os

def plot_iq_grid(samples, titles, filename, main_title):
    num_samples = len(samples)
    fig, axes = plt.subplots(num_samples, 1, figsize=(10, 3 * num_samples), constrained_layout=True)
    fig.suptitle(main_title, fontsize=16)
    
    if num_samples == 1:
        axes = [axes]
        
    for i in range(num_samples):
        sample = samples[i]
        ax = axes[i]
        ax.plot(sample[0], label='I', color='blue', alpha=0.7)
        ax.plot(sample[1], label='Q', color='red', alpha=0.7)
        ax.set_title(titles[i])
        ax.set_ylim([-1.1, 1.1])
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
    
    plt.savefig(filename)
    print(f"Saved: {filename}")

def visualize_models():
    # Load the datasets
    threat_data = np.load("data/threat_dataset.npz")
    type_data = np.load("data/type_dataset.npz")
    jammer_data = np.load("data/jammer_dataset.npz")
    
    X = threat_data['X']
    
    # Indices for classes: 0-999: WiFi, 1000-1999: DJI, 2000-2999: Jammer
    
    # 1. Visualize for THREAT MODEL (Head A)
    # Class 0: Benign (WiFi), Class 1: Threat (DJI or Jammer)
    threat_samples = [X[np.random.randint(0, 1000)], X[np.random.randint(1000, 3000)]]
    threat_titles = ["Class 0: BENIGN (WiFi - Barker Pattern)", "Class 1: THREAT (DJI/Jammer - High Energy/Entropy)"]
    plot_iq_grid(threat_samples, threat_titles, "viz_model_threat.png", "Head A: Threat Detection Model")

    # 2. Visualize for TYPE MODEL (Head B)
    # 0: WiFi, 1: DJI, 2: Jammer
    type_samples = [X[np.random.randint(0, 1000)], X[np.random.randint(1000, 2000)], X[np.random.randint(2000, 3000)]]
    type_titles = ["Class 0: WiFi", "Class 1: DJI Drone", "Class 2: Jammer"]
    plot_iq_grid(type_samples, type_titles, "viz_model_type.png", "Head B: Signal Type Classification")

    # 3. Visualize for JAMMER MODEL (Head C)
    # 0: Clear (WiFi/DJI), 1: Jammer
    jammer_samples = [X[np.random.randint(0, 2000)], X[np.random.randint(2000, 3000)]]
    jammer_titles = ["Class 0: CLEAR (WiFi/DJI)", "Class 1: JAMMING (Wiener Phase Noise)"]
    plot_iq_grid(jammer_samples, jammer_titles, "viz_model_jammer.png", "Head C: Jammer Detection Model")

if __name__ == "__main__":
    if not os.path.exists("data/threat_dataset.npz"):
        print("Error: Datasets not found. Run generator first.")
    else:
        visualize_models()
