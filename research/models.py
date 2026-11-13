import math
import torch
from torch import nn

class Forecaster(nn.Module):
    def __init__(self, kind, horizon=12, hidden=32):
        super().__init__()
        self.kind, self.horizon = kind, horizon
        if kind in ('gru','lstm'):
            self.encoder = (nn.GRU if kind == 'gru' else nn.LSTM)(2, hidden, batch_first=True)
        elif kind == 'transformer':
            self.embed = nn.Linear(2, hidden)
            self.encoder = nn.TransformerEncoder(nn.TransformerEncoderLayer(
                hidden, 4, hidden*2, dropout=0.0, batch_first=True), 2)
        else:
            raise ValueError(kind)
        self.head = nn.Linear(hidden, horizon*2)

    def forward(self, observations):
        # Relative metric displacements remove arbitrary global translations.
        dx = observations[:,1:] - observations[:,:-1]
        if self.kind == 'transformer':
            x = self.embed(dx)
            pos = torch.arange(x.shape[1], device=x.device, dtype=x.dtype)[:,None]
            freq = torch.exp(torch.arange(0,x.shape[2],2,device=x.device)*(-math.log(10000)/x.shape[2]))
            pe = torch.zeros_like(x[0]); pe[:,0::2] = torch.sin(pos*freq); pe[:,1::2] = torch.cos(pos*freq)
            encoded = self.encoder(x+pe)[ :,-1]
        else:
            encoded = self.encoder(dx)[0][:,-1]
        increments = self.head(encoded).reshape(-1,self.horizon,2)
        return observations[:,-1,None,:] + increments.cumsum(dim=1)

def constant_velocity(obs, horizon):
    velocity = obs[:,-1] - obs[:,-2]
    steps = torch.arange(1,horizon+1,device=obs.device,dtype=obs.dtype)
    return obs[:,-1,None,:] + velocity[:,None,:] * steps[None,:,None]

def displacement_errors(prediction, target):
    if prediction.shape != target.shape or prediction.ndim != 3 or prediction.shape[-1] != 2:
        raise ValueError('Expected matching [batch,horizon,2] arrays')
    if not torch.isfinite(prediction).all() or not torch.isfinite(target).all():
        raise ValueError('Nonfinite predictions or targets')
    distances = torch.linalg.vector_norm(prediction-target, dim=-1)
    return distances.mean(dim=1), distances[:,-1]
