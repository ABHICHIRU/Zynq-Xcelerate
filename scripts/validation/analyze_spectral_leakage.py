import numpy as np
import matplotlib.pyplot as plt
import os
from src.utils.channelizer import apply_channelizer_2d

def compare_spectrograms():
    # Load real-time 1D
    real_data = np.load('data/realtime/test_set.npz')
    # WiFi is 0-499, DJI is 500-999, Jammer is 1000-1499
    real_wifi = real_data['X'][0]
    real_dji = real_data['X'][500]
    real_jammer = real_data['X'][1000]
    
    # Load synthetic 2D
    syn_data = np.load('data/production_2d/dataset_2d.npz')
    # WiFi 0, DJI 1000, Jammer 2000
    syn_wifi = syn_data['X'][0]
    syn_dji = syn_data['X'][1000]
    syn_jammer = syn_data['X'][2000]
    
    # Convert real to 2D
    real_wifi_2d = apply_channelizer_2d(real_wifi[0] + 1j * real_wifi[1])
    real_dji_2d = apply_channelizer_2d(real_dji[0] + 1j * real_dji[1])
    real_jammer_2d = apply_channelizer_2d(real_jammer[0] + 1j * real_jammer[1])
    
    fig, axes = plt.subplots(3, 2, figsize=(12, 12))
    
    def plot_pair(ax_row, syn, real, title):
        ax_row[0].imshow(syn[0], aspect='auto', origin='lower')
        ax_row[0].set_title(f"SYNTHETIC {title}")
        ax_row[1].imshow(real[0], aspect='auto', origin='lower')
        ax_row[1].set_title(f"REAL-TIME {title}")

    plot_pair(axes[0], syn_wifi, real_wifi_2d, "WiFi")
    plot_pair(axes[1], syn_dji, real_dji_2d, "DJI")
    plot_pair(axes[2], syn_jammer, real_jammer_2d, "Jammer")
    
    plt.tight_layout()
    plt.savefig("spectrogram_comparison.png")
    print("Comparison saved to spectrogram_comparison.png")

if __name__ == "__main__":
    compare_spectrograms()
