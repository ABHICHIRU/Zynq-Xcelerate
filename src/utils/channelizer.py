import numpy as np
import scipy.signal

class PolyphaseChannelizer:
    """
    Efficient Polyphase Filter Bank (PFB) Channelizer.
    Splits a 1D signal into multiple sub-bands (channels) more efficiently and with better
    stop-band rejection than a simple FFT.
    """
    def __init__(self, n_channels=64, taps_per_channel=4):
        self.M = n_channels
        self.L = taps_per_channel
        self.total_taps = self.M * self.L
        
        # Prototype filter: sinc windowed with Hamming
        self.h = scipy.signal.firwin(self.total_taps, 1.0/self.M, window='hamming')
        
        # Reshape for polyphase structure
        self.p_filters = self.h.reshape(self.L, self.M).T

    def process(self, x):
        """
        Process a 1D signal into M channels.
        Input x: 1D complex signal of length multiple of M.
        Returns: 2D array of shape (M, frames).
        """
        # Padding
        n_frames = len(x) // self.M
        if len(x) % self.M != 0:
            x = np.pad(x, (0, self.M - (len(x) % self.M)))
            n_frames += 1
            
        # Reshape input for polyphase decomposition
        # (n_frames, M)
        x_reshaped = x[:n_frames * self.M].reshape(n_frames, self.M)
        
        # Polyphase Filtering
        # For each channel, we apply its sub-filter
        # This can be implemented as a convolution or a matrix multiply for short filters
        filtered = np.zeros((n_frames, self.M), dtype=complex)
        
        # Simple implementation of polyphase filtering
        for m in range(self.M):
            # Extract branch input
            branch_in = x_reshaped[:, m]
            # Branch filter
            branch_h = self.p_filters[m, :]
            # Convolution
            filtered[:, m] = np.convolve(branch_in, branch_h, mode='same')
            
        # FFT to combine channels
        out = np.fft.fft(filtered, axis=1)
        
        return out.T # (M, frames)

def apply_channelizer_2d(iq_complex):
    """
    Mathematical Bridge: 1D to 2D via STFT.
    Increased resolution to 128x128 for finer feature extraction.
    """
    f, t_stft, Zxx = scipy.signal.stft(iq_complex, nperseg=64, noverlap=60, return_onesided=False, window='hann')
    
    from scipy.interpolate import interp1d
    x = np.linspace(0, 1, Zxx.shape[1])
    x_new = np.linspace(0, 1, 128)
    f_interp = interp1d(x, Zxx, axis=1, kind='linear', fill_value="extrapolate")
    Zxx_128 = f_interp(x_new)
    
    # Frequency interpolation to 128
    y = np.linspace(0, 1, Zxx_128.shape[0])
    y_new = np.linspace(0, 1, 128)
    f_interp_freq = interp1d(y, Zxx_128, axis=0, kind='linear', fill_value="extrapolate")
    Zxx_128 = f_interp_freq(y_new)
    
    mag = 10 * np.log10(np.abs(Zxx_128)**2 + 1e-10)
    phase = np.angle(Zxx_128)
    
    def robust_norm(x, x_min, x_max):
        x = np.clip(x, x_min, x_max)
        return 2 * (x - x_min) / (x_max - x_min) - 1.0

    mag_norm = robust_norm(mag, -80, 20)
    phase_norm = robust_norm(phase, -np.pi, np.pi)
    
    return np.stack([mag_norm, phase_norm], axis=0).astype(np.float32)

if __name__ == "__main__":
    # Test
    test_signal = np.random.randn(512) + 1j * np.random.randn(512)
    output = apply_channelizer_2d(test_signal)
    print(f"Channelizer output shape: {output.shape}")
