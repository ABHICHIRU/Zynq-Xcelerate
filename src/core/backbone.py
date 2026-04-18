import torch
import torch.nn as nn

class ResBlock(nn.Module):
    """Residual block to improve gradient flow and feature depth."""
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm1d(out_channels)
        
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm1d(out_channels)
            )

    def forward(self, x):
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        return self.relu(out)

class SharedBackbone(nn.Module):
    """
    SkyShield v3.5: Residual Feature Extractor.
    Designed for Zynq-7020: Robust but hardware-efficient.
    """
    def __init__(self):
        super().__init__()
        # Initial projection: Large kernel for wide RF context
        self.start = nn.Sequential(
            nn.Conv1d(2, 32, kernel_size=11, stride=2, padding=5, bias=False),
            nn.BatchNorm1d(32),
            nn.ReLU()
        )
        
        # Residual layers
        self.layer1 = ResBlock(32, 32, stride=2)
        self.layer2 = ResBlock(32, 64, stride=2)
        
        # Global Pooling
        self.gap = nn.AdaptiveAvgPool1d(1)
        
    def forward(self, x):
        x = self.start(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.gap(x)
        return x.view(x.size(0), -1) # 64-dim output
