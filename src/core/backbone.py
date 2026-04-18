import torch
import torch.nn as nn

class ResBlockPro(nn.Module):
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
    SkyShield v5.0 Pro (Optimized): ~280,000 Parameters.
    Perfectly fits ~280KB BRAM at INT8, leaving 320KB for buffers/RTL.
    """
    def __init__(self):
        super().__init__()
        self.start = nn.Sequential(
            nn.Conv1d(2, 48, kernel_size=11, stride=2, padding=5, bias=False),
            nn.BatchNorm1d(48),
            nn.ReLU()
        )
        
        # Adjusted channel widths to hit 250k-300k range
        self.stage1 = ResBlockPro(48, 48, stride=1)
        self.stage2 = ResBlockPro(48, 96, stride=2)
        self.stage3 = ResBlockPro(96, 96, stride=2)
        self.stage4 = ResBlockPro(96, 192, stride=2)
        
        self.gap = nn.AdaptiveAvgPool1d(1)
        
    def forward(self, x):
        x = self.start(x)
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.stage4(x)
        x = self.gap(x)
        return x.view(x.size(0), -1) # 192-dim
