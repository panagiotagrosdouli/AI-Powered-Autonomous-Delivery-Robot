# Experimental protocol and present evidence

A uses Nav2 DWB plus costmaps and velocity smoothing. B adds the conservative
reactive gate; C adds CV; D replaces CV with a trained neural model. A already
reacts to dynamic LiDAR obstacles through Nav2: calling A "nonreactive" would
misrepresent the baseline. Prediction benefits must be isolated from gating effects
using C versus B and D versus C, with identical gate settings.

Two static-world A navigation smoke trials executed. There are no measured
A/B/C/D pedestrian-navigation comparison results. B, C and D experiments:
**NOT EXECUTED — NO EXPERIMENTAL RESULT AVAILABLE.**

For a controlled study use the same world, robot, initial pose, generated map,
recording segment, rigid coordinate transform, sampling interval, goal and seed
for all conditions. Keep CV and neural observation/prediction time grids equal.
Declare recording-level splits before windowing and keep training scenes out of
navigation evaluation. Use independent recording/scenario groups for confidence
intervals; overlapping trajectory windows are not independent replicates.

Preserve every failure and trial timeout. Missing collision instrumentation is
unknown collision outcome, not zero. Instrument ground-truth robot/pedestrian
poses and contact events before computing collision rates and minimum pedestrian
clearance. Distinguish wheel-odometry path length from ground-truth path length.
Record intervention transitions, action outcomes, simulated duration and wall
runtime separately. D must use a genuine real-data checkpoint with provenance.

`research.trials` validates matched scenario/seed sets and includes failed trials.
It computes descriptive means/standard deviations and Wilson 95% intervals for
binary outcomes. It rejects unknown outcomes or missing measurements instead of
silently excluding failed trials. It has only fixture tests, not research trial
inputs yet. No research confidence intervals are reported.

See SYNTHETIC_RESULTS.md for actual software-fixture ADE/FDE/latency measurements.
These cannot answer the pedestrian-navigation hypothesis.
