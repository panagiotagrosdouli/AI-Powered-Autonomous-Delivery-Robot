"""Displacement metrics and a deterministic constant-velocity baseline."""

from __future__ import annotations

import math
from collections.abc import Sequence

Point = tuple[float, float]


def constant_velocity(observation: Sequence[Point], steps: int) -> tuple[Point, ...]:
    if len(observation) < 2 or steps < 1:
        raise ValueError("Need two observations and at least one forecast step")
    dx = observation[-1][0] - observation[-2][0]
    dy = observation[-1][1] - observation[-2][1]
    x, y = observation[-1]
    return tuple((x + k * dx, y + k * dy) for k in range(1, steps + 1))


def displacement_errors(prediction: Sequence[Point], target: Sequence[Point]) -> tuple[float, float]:
    if not prediction or len(prediction) != len(target):
        raise ValueError("Prediction and target must have the same nonzero length")
    errors = [math.hypot(px - tx, py - ty) for (px, py), (tx, ty) in zip(prediction, target)]
    return sum(errors) / len(errors), errors[-1]


def evaluate_constant_velocity(windows) -> dict[str, float | int]:
    if not windows:
        raise ValueError("No trajectory windows available for evaluation")
    scores = [displacement_errors(constant_velocity(w.observation, len(w.future)), w.future)
              for w in windows]
    return {"windows": len(scores), "ADE_m": sum(a for a, _ in scores) / len(scores),
            "FDE_m": sum(f for _, f in scores) / len(scores)}
