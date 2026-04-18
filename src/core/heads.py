import torch
import torch.nn as nn

class UnifiedHead(nn.Module):
    """Deep head for robust classification."""
    def __init__(self, in_features=64, hidden=32, out_classes=1):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(hidden, out_classes)
        )
    def forward(self, x):
        return self.fc(x)

# Keeping old names for pipeline compatibility
class ThreatHead(UnifiedHead):
    def __init__(self, in_features=64):
        super().__init__(in_features=in_features, out_classes=1)

class TypeHead(UnifiedHead):
    def __init__(self, in_features=64):
        super().__init__(in_features=in_features, out_classes=3)

class JammerHead(UnifiedHead):
    def __init__(self, in_features=64):
        super().__init__(in_features=in_features, out_classes=1)
