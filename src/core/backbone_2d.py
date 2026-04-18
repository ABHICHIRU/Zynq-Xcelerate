import torch
import torch.nn as nn
import torch.nn.functional as F

class ResBlock2d(nn.Module):
    """Residual Block for 2D RF Representations."""
    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        return F.relu(out)

class GlobalContextBlock(nn.Module):
    """Global Context to capture long-range spectral dependencies."""
    def __init__(self, in_channels):
        super().__init__()
        self.conv_mask = nn.Conv2d(in_channels, 1, kernel_size=1)
        self.softmax = nn.Softmax(dim=2)
        self.channel_add_conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels // 4, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels // 4, in_channels, kernel_size=1)
        )

    def forward(self, x):
        batch, channels, height, width = x.size()
        input_x = x.view(batch, channels, height * width).unsqueeze(1)
        mask = self.conv_mask(x).view(batch, 1, height * width)
        mask = self.softmax(mask).unsqueeze(-1)
        context = torch.matmul(input_x, mask).view(batch, channels, 1, 1)
        return x + self.channel_add_conv(context)

class SharedBackbone2d(nn.Module):
    """
    SkyShield v6.0 Echelon: Global-Context Hybrid 2D ResNet.
    Optimized for Zynq-7020 FPGA constraints.
    """
    def __init__(self):
        super().__init__()
        # Input: (2, 128, 128) - Mag & Phase
        self.start = nn.Sequential(
            nn.Conv2d(2, 48, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(48),
            nn.ReLU()
        )
        
        self.layer1 = ResBlock2d(48, 48, stride=1)
        self.gc1 = GlobalContextBlock(48)
        
        self.layer2 = ResBlock2d(48, 96, stride=2)
        self.gc2 = GlobalContextBlock(96)
        
        self.layer3 = ResBlock2d(96, 192, stride=2)
        
        self.gap = nn.AdaptiveAvgPool2d(1)
        
    def forward(self, x):
        x = self.start(x)
        x = self.gc1(self.layer1(x))
        x = self.gc2(self.layer2(x))
        x = self.layer3(x)
        x = self.gap(x)
        return x.view(x.size(0), -1) # 192-dim features

# Keep variants for benchmarking purposes if needed, but SharedBackbone2d is primary
BackboneV1_Balanced = SharedBackbone2d # Alias for compatibility
