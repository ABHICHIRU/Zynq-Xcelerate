import torch
import torch.nn as nn

class SharedBackbone(nn.Module):
    """
    Shared 1D-CNN Feature Extractor for Zynq-7020 FPGA acceleration.
    Constraints: INT8 Quantizable, No FFT, Minimal FPU usage.
    """
    def __init__(self):
        super(SharedBackbone, self).__init__()
        # Input: (Batch, 2, 512)
        # Conv1D(2 -> 16)
        self.conv1 = nn.Conv1d(in_channels=2, out_channels=16, kernel_size=7, stride=2, padding=3)
        self.relu1 = nn.ReLU()
        
        # DepthwiseConv1D (Separable convolution for efficiency)
        self.depthwise = nn.Conv1d(in_channels=16, out_channels=16, kernel_size=3, stride=1, padding=1, groups=16)
        
        # Conv1D(16 -> 32)
        self.conv2 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=3, stride=2, padding=1)
        self.relu2 = nn.ReLU()
        
        # Global Average Pooling (Standard feature reduction)
        self.gap = nn.AdaptiveAvgPool1d(1)
        
    def forward(self, x):
        x = self.relu1(self.conv1(x))
        x = self.depthwise(x)
        x = self.relu2(self.conv2(x))
        x = self.gap(x)
        return x.view(x.size(0), -1) # Flattened 32-dim feature vector
