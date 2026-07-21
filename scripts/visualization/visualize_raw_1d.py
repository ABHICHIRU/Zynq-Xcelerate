import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.fftpack
from src.data_pipeline.generator_2d import generate_wifi_dsss, generate_dji_pulse, generate_jammer

def visualize_raw_physics():
    snr_test = 10 # Clear signal for visualization
    
    signals = {
        "WiFi (802.11b DSSS)": generate_wifi_dsss(snr_test),
        "DJI Pulse (Multitone)": generate_dji_pulse(snr_test),
        "Jammer (Wiener Phase)": generate_jammer(snr_test)
    }
    
    fig, axes = plt.subplots(3, 2, figsize=(15, 12))
    plt.subplots_adjust(hspace=0.4, wspace=0.3)
    
    for i, (name, iq) in enumerate(signals.items()):
        t = np.arange(512)
        
        # --- Time Domain Plot ---
        axes[i, 0].plot(t, iq.real, label='I (Real)', alpha=0.7)
        axes[i, 0].plot(t, iq.imag, label='Q (Imag)', alpha=0.7)
        axes[i, 0].set_title(f"{name} - Time Domain (Raw IQ)")
        axes[i, 0].set_xlabel("Sample Index")
        axes[i, 0].set_ylabel("Amplitude")
        axes[i, 0].legend(loc='upper right')
        axes[i, 0].grid(True, alpha=0.3)
        
        # --- Frequency Domain Plot (PSD) ---
        iq_fft = scipy.fftpack.fft(iq)
        psd = 10 * np.log10(np.abs(scipy.fftpack.fftshift(iq_fft))**2 + 1e-9)
        freqs = np.linspace(-0.5, 0.5, 512)
        
        axes[i, 1].plot(freqs, psd, color='red')
        axes[i, 1].set_title(f"{name} - Power Spectral Density (PSD)")
        axes[i, 1].set_xlabel("Normalized Frequency")
        axes[i, 1].set_ylabel("Power (dB)")
        axes[i, 1].grid(True, alpha=0.3)
        
        # Highlighting Physics Features
        if "WiFi" in name:
            axes[i, 0].set_title(f"{name}\n(Physics: 11-chip Barker Code Phase Shifts)")
        elif "DJI" in name:
            axes[i, 0].set_title(f"{name}\n(Physics: Gaussian Slew Envelope + Multitone)")
        elif "Jammer" in name:
            axes[i, 0].set_title(f"{name}\n(Physics: Wiener Process Random Walk Phase)")

    plt.suptitle("SkyShield v4.0 Raw 1D Physics-Based Signal Generation\n(Before 2D Preprocessing)", fontsize=16)
    
    output_file = "viz_raw_1d_physics.png"
    plt.savefig(output_file)
    print(f"Raw 1D visualization saved to {output_file}")
    plt.show()

if __name__ == "__main__":
    visualize_raw_physics()
