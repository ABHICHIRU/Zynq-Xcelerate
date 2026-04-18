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
    Bridge function to use PolyphaseChannelizer and return (2, 64, 64) tensor.
    """
    # Using 64 channels
    pfb = PolyphaseChannelizer(n_channels=64)
    # We need to pad iq_complex to get 64 frames
    # 64 * 64 = 4096. Original is 512.
    # To get 64 frames with 64 channels, we need 4096 samples.
    # We can zero-pad or repeat.
    padded = np.pad(iq_complex, (0, 4096 - len(iq_complex)), mode='constant')
    
    channels = pfb.process(padded) # (64, 64)
    
    # Extract Channels (Magnitude and Phase)
    mag = 10 * np.log10(np.abs(channels)**2 + 1e-9)
    phase = np.angle(channels)
    
    # Normalization to [-1, 1]
    def min_max_norm(x):
        xmin, xmax = x.min(), x.max()
        if xmax == xmin: return x * 0
        return 2 * (x - xmin) / (xmax - xmin) - 1.0

    mag_norm = min_max_norm(mag)
    phase_norm = min_max_norm(phase)
    
    return np.stack([mag_norm, phase_norm], axis=0).astype(np.float32)

if __name__ == "__main__":
    # Test
    test_signal = np.random.randn(512) + 1j * np.random.randn(512)
    output = apply_channelizer_2d(test_signal)
    print(f"Channelizer output shape: {output.shape}")
