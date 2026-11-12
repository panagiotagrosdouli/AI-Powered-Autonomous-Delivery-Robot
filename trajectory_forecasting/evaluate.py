"""Evaluate the non-learned baseline on an explicitly selected scene split."""

import argparse
import json
from pathlib import Path

from .data import load_windows
from .metrics import evaluate_constant_velocity


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="CSV with scene_id,pedestrian_id,frame,x,y")
    parser.add_argument("--scenes", nargs="+", required=True, help="held-out scene IDs")
    parser.add_argument("--observation-frames", type=int, default=8)
    parser.add_argument("--prediction-frames", type=int, default=12)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    windows = load_windows(args.csv, set(args.scenes), args.observation_frames,
                           args.prediction_frames, args.stride)
    result = {"method": "constant_velocity", "scenes": sorted(set(args.scenes)),
              "observation_frames": args.observation_frames,
              "prediction_frames": args.prediction_frames,
              "metrics": evaluate_constant_velocity(windows)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
