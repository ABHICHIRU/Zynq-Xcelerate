import torch
import torch.nn as nn

class UnifiedHeadPro2d(nn.Module):
    """Deep Pro-tier head for 2D architecture."""
    def __init__(self, in_features=256, hidden=64, out_classes=1):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden, out_classes)
        )
    def forward(self, x):
        return self.fc(x)

class ThreatHead2d(UnifiedHeadPro2d):
    def __init__(self, in_features=256):
        super().__init__(in_features=in_features, out_classes=1)

class TypeHead2d(UnifiedHeadPro2d):
    def __init__(self, in_features=256):
        super().__init__(in_features=in_features, out_classes=3)

class JammerHead2d(UnifiedHeadPro2d):
    def __init__(self, in_features=256):
        super().__init__(in_features=in_features, out_classes=1)
