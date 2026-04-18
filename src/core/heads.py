import torch
import torch.nn as nn

class ThreatHead(nn.Module):
    """Head A: Binary Classification (Benign/Threat)"""
    def __init__(self, input_dim=32):
        super(ThreatHead, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1) # Output raw logit
        )
    def forward(self, x):
        return self.fc(x)

class TypeHead(nn.Module):
    """Head B: 3-Class Classification (WiFi/DJI/Jammer)"""
    def __init__(self, input_dim=32):
        super(TypeHead, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 3) # WiFi=0, DJI=1, Jammer=2
        )
    def forward(self, x):
        return self.fc(x)

class JammerHead(nn.Module):
    """Head C: Binary Classification (Clear/Jammer)"""
    def __init__(self, input_dim=32):
        super(JammerHead, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 1) # Output raw logit
        )
    def forward(self, x):
        return self.fc(x)
