"""Optional PyTorch GRU, LSTM and Transformer trajectory forecasters.

Models predict coordinate offsets relative to the final observed position.
PyTorch is an optional training dependency and is not required by the baseline.
"""

try:
    import torch
    from torch import nn
except ImportError as exc:  # pragma: no cover - depends on optional dependency
    torch = None
    nn = None
    _TORCH_ERROR = exc


def _require_torch():
    if torch is None:
        raise RuntimeError("Learned trajectory models require PyTorch; install the optional training dependencies") from _TORCH_ERROR


if nn is not None:
    class RecurrentForecaster(nn.Module):
        def __init__(self, kind: str, prediction_frames: int, hidden_size: int = 64):
            super().__init__()
            if kind not in {"gru", "lstm"}:
                raise ValueError("kind must be 'gru' or 'lstm'")
            self.kind = kind
            self.encoder = nn.GRU(2, hidden_size, batch_first=True) if kind == "gru" else nn.LSTM(2, hidden_size, batch_first=True)
            self.head = nn.Linear(hidden_size, prediction_frames * 2)
            self.prediction_frames = prediction_frames

        def forward(self, points):
            _, state = self.encoder(points)
            hidden = state[0] if self.kind == "lstm" else state
            offsets = self.head(hidden[-1]).view(-1, self.prediction_frames, 2)
            return offsets + points[:, -1:, :]


    class TransformerForecaster(nn.Module):
        def __init__(self, prediction_frames: int, hidden_size: int = 64, heads: int = 4):
            super().__init__()
            if hidden_size % heads:
                raise ValueError("hidden_size must be divisible by heads")
            self.input = nn.Linear(2, hidden_size)
            layer = nn.TransformerEncoderLayer(hidden_size, heads, hidden_size * 2,
                                               batch_first=True, norm_first=True)
            self.encoder = nn.TransformerEncoder(layer, num_layers=2)
            self.head = nn.Linear(hidden_size, prediction_frames * 2)
            self.prediction_frames = prediction_frames

        def forward(self, points):
            encoded = self.encoder(self.input(points))
            offsets = self.head(encoded[:, -1]).view(-1, self.prediction_frames, 2)
            return offsets + points[:, -1:, :]
else:
    class RecurrentForecaster:  # pragma: no cover - depends on optional dependency
        def __init__(self, *args, **kwargs):
            _require_torch()

    class TransformerForecaster:  # pragma: no cover - depends on optional dependency
        def __init__(self, *args, **kwargs):
            _require_torch()


def create_model(name: str, prediction_frames: int):
    _require_torch()
    if name in {"gru", "lstm"}:
        return RecurrentForecaster(name, prediction_frames)
    if name == "transformer":
        return TransformerForecaster(prediction_frames)
    raise ValueError(f"Unknown model: {name}")
