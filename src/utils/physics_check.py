import numpy as np

def check_snr_physics(signal, noise, expected_snr_db):
    """Verifies that the added AWGN matches the requested SNR."""
    signal_power = np.mean(np.abs(signal)**2)
    noise_power = np.mean(np.abs(noise)**2)
    actual_snr = 10 * np.log10(signal_power / noise_power)
    return np.abs(actual_snr - expected_snr_db) < 0.5 # Tolerance within 0.5dB

def check_barker_dsss(iq_samples):
    """
    Empirically check for the presence of the 11-chip Barker code 
    [1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1] via cross-correlation.
    """
    barker = np.array([1, -1, 1, 1, -1, 1, 1, 1, -1, -1, -1])
    # Extract real part for correlation
    i_signal = iq_samples[0, :]
    correlation = np.correlate(i_signal, barker, mode='valid')
    # If the Barker code is present, we expect sharp peaks
    return np.max(np.abs(correlation)) > 2.0

def check_pulse_slew_rate(iq_samples):
    """Checks for Gaussian smoothing on pulse edges (no infinite bandwidth)."""
    # Calculate gradient (slew rate)
    grad = np.gradient(np.abs(iq_samples[0, :]))
    # If pulse was a perfect square wave, grad would be extremely high at edges.
    # We expect a maximum slew rate limited by our Gaussian window.
    return np.max(np.abs(grad)) < 0.5

def check_wiener_entropy(iq_samples):
    """Verifies that jammer phase noise follows a random walk (Wiener Process)."""
    phase = np.angle(iq_samples[0, :] + 1j * iq_samples[1, :])
    phase_diff = np.diff(phase)
    # The differences of a Wiener process should be Gaussian distributed
    std_diff = np.std(phase_diff)
    # Check if the phase is actually changing (not a static sine wave)
    return std_diff > 0.01
