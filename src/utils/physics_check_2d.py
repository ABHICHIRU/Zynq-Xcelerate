import numpy as np

def check_spectral_leakage(spectrogram, threshold=-40):
    """
    Checks if there's excessive spectral leakage in the spectrogram.
    Leakage is checked by looking at the noise floor in the frequency domain.
    """
    # Assuming channel 0 is Magnitude in dB
    mag = spectrogram[0]
    # Simple check: if the mean of the bottom 10% of values is too high, 
    # it might indicate poor windowing or interpolation artifacts.
    noise_floor = np.partition(mag.flatten(), int(0.1 * mag.size))[:int(0.1 * mag.size)]
    mean_noise = np.mean(noise_floor)
    return mean_noise < threshold

def check_tf_resolution(spectrogram, expected_shape=(2, 128, 128)):
    """Verifies the Time-Frequency resolution matches system constraints."""
    return spectrogram.shape == expected_shape

def check_normalization_2d(spectrogram):
    """Ensures spectrogram values are within [-1, 1] for INT8 safety."""
    return np.all(spectrogram >= -1.0) and np.all(spectrogram <= 1.0)

def verify_physics_2d(spectrogram):
    """Comprehensive 2D physics check."""
    results = {
        "spectral_leakage_ok": check_spectral_leakage(spectrogram),
        "tf_resolution_ok": check_tf_resolution(spectrogram),
        "normalization_ok": check_normalization_2d(spectrogram)
    }
    return results, all(results.values())
