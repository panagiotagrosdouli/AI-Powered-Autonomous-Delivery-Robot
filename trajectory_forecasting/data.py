"""Scene-separated loading of metric pedestrian trajectories from CSV.

CSV columns: scene_id, pedestrian_id, frame, x, y. Coordinates must be metres
in a consistent Cartesian frame; rows are never mixed across scene IDs.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrajectoryWindow:
    scene_id: str
    pedestrian_id: str
    observation: tuple[tuple[float, float], ...]
    future: tuple[tuple[float, float], ...]


def read_tracks(path: str | Path) -> dict[tuple[str, str], list[tuple[int, float, float]]]:
    """Read and validate the documented CSV format without imputing missing rows."""
    tracks: dict[tuple[str, str], list[tuple[int, float, float]]] = defaultdict(list)
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {"scene_id", "pedestrian_id", "frame", "x", "y"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV must contain columns: {', '.join(sorted(required))}")
        for line, row in enumerate(reader, start=2):
            try:
                scene, person = row["scene_id"].strip(), row["pedestrian_id"].strip()
                frame = int(row["frame"])
                x, y = float(row["x"]), float(row["y"])
            except (AttributeError, TypeError, ValueError) as exc:
                raise ValueError(f"Invalid trajectory row at line {line}") from exc
            if not scene or not person or not math.isfinite(x) or not math.isfinite(y):
                raise ValueError(f"Invalid identity or non-finite coordinate at line {line}")
            tracks[(scene, person)].append((frame, x, y))

    for identity, rows in tracks.items():
        rows.sort(key=lambda row: row[0])
        frames = [row[0] for row in rows]
        if len(set(frames)) != len(frames):
            raise ValueError(f"Duplicate frame for trajectory {identity}")
    return dict(tracks)


def load_windows(
    path: str | Path,
    scene_ids: set[str] | frozenset[str],
    observation_frames: int = 8,
    prediction_frames: int = 12,
    stride: int = 1,
) -> list[TrajectoryWindow]:
    """Build contiguous windows only from explicitly selected scenes."""
    if observation_frames < 2 or prediction_frames < 1 or stride < 1:
        raise ValueError("Need >=2 observed frames, >=1 future frame, and positive stride")
    windows = []
    size = observation_frames + prediction_frames
    for (scene, person), rows in read_tracks(path).items():
        if scene not in scene_ids:
            continue
        for start in range(0, len(rows) - size + 1, stride):
            sample = rows[start : start + size]
            # Do not bridge dropped frames: frame spacing must be uniform.
            frame_steps = [sample[i + 1][0] - sample[i][0] for i in range(size - 1)]
            if len(set(frame_steps)) != 1:
                continue
            coords = tuple((row[1], row[2]) for row in sample)
            windows.append(TrajectoryWindow(scene, person, coords[:observation_frames],
                                            coords[observation_frames:]))
    return windows
