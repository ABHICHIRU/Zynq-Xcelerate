import torch
import torch.nn as nn
import torch.nn.functional as F

class DualStreamHarmonizer(nn.Module):
    """
    Initial stage that allows Phase (Ch 1) and Magnitude (Ch 0) to interact.
    Uses an attention-gate to filter noise based on phase-consistency.
    """
    def __init__(self, in_channels=2, out_channels=64):
        super().__init__()
        self.conv_mag = nn.Conv2d(1, out_channels // 2, kernel_size=3, padding=1, bias=False)
        self.conv_phs = nn.Conv2d(1, out_channels // 2, kernel_size=3, padding=1, bias=False)
        self.gate = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, kernel_size=1, bias=False),
            nn.Sigmoid()
        )
        self.out_conv = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=2, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        mag = self.conv_mag(x[:, 0:1, :, :])
        phs = self.conv_phs(x[:, 1:2, :, :])
        combined = torch.cat([mag, phs], dim=1)
        gated = combined * self.gate(combined)
        return F.relu(self.bn(self.out_conv(gated)))

class GlobalContextBlock(nn.Module):
    """
    Simplified Non-Local block to capture long-range spectral dependencies.
    Essential for detecting wideband sweeping jammers.
    """
    def __init__(self, in_channels):
        super().__init__()
        self.conv_mask = nn.Conv2d(in_channels, 1, kernel_size=1)
        self.softmax = nn.Softmax(dim=2)
        self.channel_add_conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels // 4, kernel_size=1),
            nn.LayerNorm([in_channels // 4, 1, 1]),
            nn.ReLU(inplace=True),
            nn.Conv2d(in_channels // 4, in_channels, kernel_size=1)
        )

    def forward(self, x):
        batch, channels, height, width = x.size()
        input_x = x.view(batch, channels, height * width)
        input_x = input_x.unsqueeze(1)
        
        mask = self.conv_mask(x).view(batch, 1, height * width)
        mask = self.softmax(mask).unsqueeze(-1)
        
        context = torch.matmul(input_x, mask).view(batch, channels, 1, 1)
        return x + self.channel_add_conv(context)

class DenseResidualElite(nn.Module):
    """Dense-Residual Block with Dilation for Multi-Scale Feature Aggregation."""
    def __init__(self, in_channels, out_channels, dilation=1):
        super().__init__()
        mid = out_channels // 2
        self.conv1 = nn.Conv2d(in_channels, mid, kernel_size=3, padding=dilation, dilation=dilation, bias=False)
        self.bn1 = nn.BatchNorm2d(mid)
        self.conv2 = nn.Conv2d(mid + in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.gc = GlobalContextBlock(out_channels)
        
        self.shortcut = nn.Sequential()
        if in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        out1 = F.relu(self.bn1(self.conv1(x)))
        # Dense connection
        combined = torch.cat([x, out1], dim=1)
        out2 = self.bn2(self.conv2(combined))
        out2 = self.gc(out2)
        return F.relu(out2 + self.shortcut(x))

class SharedBackbone2d(nn.Module):
    """
    SkyShield v6.0 Echelon: Global-Context Hybrid Dense-ResNet.
    Engineered for 'Elite' tier complexity and real-world RF survival.
    Input Shape: (2, 128, 128)
    """
    def __init__(self):
        super().__init__()
        # Level 1: Harmonized Input (128x128 -> 64x64)
        self.harmonizer = DualStreamHarmonizer(2, 64)
        
        # Level 2: High-Resolution Processing (64x64)
        self.stage1 = DenseResidualElite(64, 64, dilation=1)
        
        # Level 3: Spectral Transition (64x64 -> 32x32)
        self.down1 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False)
        self.stage2 = DenseResidualElite(128, 128, dilation=2)
        
        # Level 4: Wideband Isolation (32x32 -> 16x16)
        self.down2 = nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1, bias=False)
        self.stage3 = DenseResidualElite(256, 256, dilation=4)
        
        # Level 5: Deep Semantic Bottleneck (16x16 -> 8x8)
        self.down3 = nn.Conv2d(256, 1024, kernel_size=3, stride=2, padding=1, bias=False)
        self.stage4 = DenseResidualElite(1024, 1024, dilation=1)
        
        self.gap = nn.AdaptiveAvgPool2d(1)
        
    def forward(self, x):
        x = self.harmonizer(x)
        x = self.stage1(x)
        x = self.down1(x)
        x = self.stage2(x)
        x = self.down2(x)
        x = self.stage3(x)
        x = self.down3(x)
        x = self.stage4(x)
        x = self.gap(x)
        return x.view(x.size(0), -1) # 1024-dim feature vector
