# Evaluation protocol

Evaluate with matched world seeds, robot geometry, goals, pedestrian paths and navigation parameters.

**Baselines:** Nav2 alone; Nav2 + laser gate; Nav2 + laser gate + constant-velocity predictions. Future research: a trained GRU or Transformer instead of constant velocity.

**Metrics:** goal success rate, collisions per trial, minimum pedestrian clearance, route completion time, safety-gate interventions, p95 inference latency, forecast ADE and FDE.

For any reported result: publish number of trials, mean and dispersion, confidence intervals, scenario splits and hardware. Evaluate stochastic models on held-out scenarios. Count unsuccessful runs, not only completed runs.

**Current status:** no simulator results have been measured. Python unit tests only check algorithm behavior; they do not establish collision avoidance performance.
