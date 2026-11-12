"""Train and evaluate a learned trajectory forecaster on scene-disjoint splits."""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path

from .data import load_windows
from .models import create_model, torch


def _scene_sets(train_scenes: list[str], val_scenes: list[str]) -> None:
    if not train_scenes or not val_scenes:
        raise ValueError("Provide at least one training scene and one validation scene")
    overlap = set(train_scenes) & set(val_scenes)
    if overlap:
        raise ValueError(f"Training and validation scenes must be disjoint: {sorted(overlap)}")


def _metric_batch(prediction, target):
    errors = ((prediction - target) ** 2).sum(dim=-1).sqrt()
    return errors.mean().item(), errors[:, -1].mean().item()


def train(args) -> dict:
    if torch is None:
        raise RuntimeError("Training requires PyTorch; install trajectory_forecasting/requirements-train.txt")
    _scene_sets(args.train_scenes, args.val_scenes)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    device = torch.device("cuda" if args.device == "auto" and torch.cuda.is_available()
                          else "cpu" if args.device == "auto" else args.device)

    train_windows = load_windows(args.csv, set(args.train_scenes), args.observation_frames,
                                 args.prediction_frames, args.stride)
    val_windows = load_windows(args.csv, set(args.val_scenes), args.observation_frames,
                               args.prediction_frames, args.stride)
    if not train_windows or not val_windows:
        raise ValueError(f"No windows for selected splits (train={len(train_windows)}, val={len(val_windows)})")

    x_train = torch.tensor([w.observation for w in train_windows], dtype=torch.float32)
    y_train = torch.tensor([w.future for w in train_windows], dtype=torch.float32)
    x_val = torch.tensor([w.observation for w in val_windows], dtype=torch.float32, device=device)
    y_val = torch.tensor([w.future for w in val_windows], dtype=torch.float32, device=device)
    model = create_model(args.model, args.prediction_frames).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / f"{args.model}_best.pt"
    history = []
    best_ade = float("inf")
    generator = torch.Generator().manual_seed(args.seed)

    for epoch in range(1, args.epochs + 1):
        model.train()
        order = torch.randperm(len(x_train), generator=generator)
        for start in range(0, len(order), args.batch_size):
            indices = order[start:start + args.batch_size]
            observed = x_train[indices].to(device)
            target = y_train[indices].to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = torch.nn.functional.mse_loss(model(observed), target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

        model.eval()
        with torch.no_grad():
            prediction = model(x_val)
            val_ade, val_fde = _metric_batch(prediction, y_val)
        row = {"epoch": epoch, "validation_ADE_m": val_ade, "validation_FDE_m": val_fde}
        history.append(row)
        print(json.dumps(row))
        if val_ade < best_ade:
            best_ade = val_ade
            torch.save({"model": args.model, "state_dict": model.state_dict(),
                        "observation_frames": args.observation_frames,
                        "prediction_frames": args.prediction_frames,
                        "train_scenes": sorted(set(args.train_scenes)),
                        "validation_scenes": sorted(set(args.val_scenes)),
                        "seed": args.seed}, checkpoint)

    with checkpoint.open("rb") as stream:
        model_bytes = len(stream.read())
    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True)["state_dict"])
    model.eval()
    # Warm-up and repeated forward passes make the timing protocol explicit.
    with torch.no_grad():
        sample = x_val[:1]
        for _ in range(10):
            model(sample)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        repeats = max(100, args.latency_repeats)
        start = time.perf_counter()
        for _ in range(repeats):
            model(sample)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        latency_ms = (time.perf_counter() - start) * 1000.0 / repeats
        prediction = model(x_val)
        ade, fde = _metric_batch(prediction, y_val)

    result = {"model": args.model, "seed": args.seed, "device": str(device),
              "train_scenes": sorted(set(args.train_scenes)),
              "validation_scenes": sorted(set(args.val_scenes)),
              "observation_frames": args.observation_frames,
              "prediction_frames": args.prediction_frames,
              "sampling_period_seconds": args.sampling_period,
              "train_windows": len(train_windows), "validation_windows": len(val_windows),
              "validation_ADE_m": ade, "validation_FDE_m": fde,
              "inference_latency_ms_per_window": latency_ms, "checkpoint_bytes": model_bytes,
              "latency_protocol": f"10 warmups then {repeats} single-window forwards; batch=1"}
    (output / "metrics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with (output / "history.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["epoch", "validation_ADE_m", "validation_FDE_m"])
        writer.writeheader()
        writer.writerows(history)
    print(json.dumps(result, indent=2))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--train-scenes", nargs="+", required=True)
    parser.add_argument("--val-scenes", nargs="+", required=True)
    parser.add_argument("--model", choices=["gru", "lstm", "transformer"], required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--observation-frames", type=int, default=8)
    parser.add_argument("--prediction-frames", type=int, default=12)
    parser.add_argument("--sampling-period", type=float, required=True,
                        help="seconds between source frames; recorded as provenance")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--latency-repeats", type=int, default=500)
    args = parser.parse_args(argv)
    if args.sampling_period <= 0 or args.epochs < 1 or args.batch_size < 1:
        parser.error("sampling-period, epochs, and batch-size must be positive")
    train(args)


if __name__ == "__main__":
    main()
