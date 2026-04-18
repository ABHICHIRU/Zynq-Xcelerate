import torch
import torch.nn as nn

class UnifiedHeadElite2d(nn.Module):
    """Elite-tier head for 1024-dim feature vectors."""
    def __init__(self, in_features=1024, hidden=256, out_classes=1):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(hidden, hidden // 2),
            nn.BatchNorm1d(hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, out_classes)
        )
    def forward(self, x):
        return self.fc(x)

class ThreatHead2d(UnifiedHeadElite2d):
    def __init__(self, in_features=1024):
        super().__init__(in_features=in_features, out_classes=1)

class TypeHead2d(UnifiedHeadElite2d):
    def __init__(self, in_features=1024):
        super().__init__(in_features=in_features, out_classes=3)

class JammerHead2d(UnifiedHeadElite2d):
    def __init__(self, in_features=1024):
        super().__init__(in_features=in_features, out_classes=1)
