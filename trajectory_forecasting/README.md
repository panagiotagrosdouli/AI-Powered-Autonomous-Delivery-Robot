# Pedestrian trajectory forecasting

This package provides a constant-velocity reference baseline, a scene-separated
trajectory-window loader, ADE/FDE evaluation, and optional PyTorch GRU, LSTM and
Transformer model architectures. Coordinates are Cartesian metres. The default
window uses 8 observed and 12 future frames; the sampling period must be recorded
for each source dataset because a frame is not a fixed duration across datasets.

## Data format and split discipline

Provide a CSV with `scene_id,pedestrian_id,frame,x,y`. `frame` must be an integer
index and positions must already be in metric Cartesian coordinates. The loader
rejects duplicate frames, non-finite coordinates and windows crossing missing
frames. Select complete scene IDs for each split; never split overlapping windows
randomly. For example, keep one or more entire scenes aside for validation and
test before building windows.

Run the baseline on held-out scenes:

```sh
python -m trajectory_forecasting.evaluate path/to/tracks.csv \
  --scenes heldout_scene_1 heldout_scene_2 --output results/baseline.json
```

The output is generated only from the provided input data. No scores or trained
weights are included in this repository. Model classes require PyTorch, but the
constant-velocity baseline and CSV validation use only the Python standard library.

## Dataset provenance and restrictions

No dataset is bundled or downloaded by this package. Before using ETH/UCY, SDD,
or another benchmark, obtain it from its official project source, verify the
current research/commercial use terms, document the source URL, access date,
license/terms, checksum, coordinate units and frame sampling rate, and keep the
raw data outside version control unless redistribution is explicitly permitted.
Do not assume that public download availability grants redistribution rights.

The `scene_id` column should preserve the original scene identity so that splits
can be reproduced and leakage can be audited. The package does not claim any
benchmark result or real-world navigation performance.
