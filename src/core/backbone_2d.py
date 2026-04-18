import torch
import torch.nn as nn

class DepthwiseSeparableConv2d(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0):
        super().__init__()
        self.depthwise = nn.Conv2d(in_channels, in_channels, kernel_size=kernel_size, 
                                   stride=stride, padding=padding, groups=in_channels, bias=False)
        self.pointwise = nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.depthwise(x)
        x = self.pointwise(x)
        x = self.bn(x)
        return self.relu(x)

class ResBlock2d(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = DepthwiseSeparableConv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.conv2 = DepthwiseSeparableConv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        out = self.conv1(x)
        out = self.conv2(out)
        out = out + self.shortcut(x)
        return torch.relu(out)

class SharedBackbone2d(nn.Module):
    """
    SkyShield v4.0 2D: Depthwise-Separable CNN for Zynq-7020.
    Optimized for Tensor Shape (2, 64, 64).
    """
    def __init__(self):
        super().__init__()
        self.start = nn.Sequential(
            nn.Conv2d(2, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU()
        ) # 32x32
        
        self.stage1 = ResBlock2d(32, 32, stride=1)
        self.stage2 = ResBlock2d(32, 64, stride=2) # 16x16
        self.stage3 = ResBlock2d(64, 128, stride=2) # 8x8
        self.stage4 = ResBlock2d(128, 256, stride=2) # 4x4
        
        self.gap = nn.AdaptiveAvgPool2d(1)
        
    def forward(self, x):
        x = self.start(x)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.stage4(x)
        x = self.gap(x)
        return x.view(x.size(0), -1) # 256-dim
