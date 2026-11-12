# Mandatory delivery status — 2026-11-12

**Overall: INCOMPLETE research project.** No evidence yet establishes a benefit
from learned pedestrian prediction. Measured simulation smoke tests are kept
separate from synthetic model tests and unexecuted research experiments.

## IMPLEMENTED

Custom differential-drive Xacro robot with collision/inertial geometry, driven
wheels, passive casters, LiDAR and RGB-D; indoor/outdoor SDF worlds; Gazebo/ROS
bridges; mapping launch/config; AMCL/Nav2 launch/config with planner, DWB,
costmaps, behavior tree, recoveries, velocity smoothing and waypoint follower.
Stamped forecast interfaces preserve IDs, frames, observation time and horizons.
CV tracker, conservative all-around reactive/forecast gate and optional trained
checkpoint adapter implement B/C/D routing after the smoother. YOLO offline
inference, metric geometry utilities, archive inspection, recording-level split
validation, GRU/LSTM/Transformer training/evaluation, replay utilities, matched
trial aggregation, tests, CI and programmatic evidence figures are supplied.
Implementation does not imply runtime verification of every mode.

## EXECUTED

- Repository audit of baseline 6e8c8a3 and six original algorithm tests.
- Official Jazzy image pulls, staged apt installs, actual colcon builds/tests.
- `scripts/test_simulation.py` against a running custom Gazebo robot.
- `scripts/test_mapping.py` against actual SLAM Toolbox and simulated sensors.
- Two `scripts/test_navigation.py` runs against AMCL and Nav2 using the new map.
- Isolated ROS transport test with synthetic detection/scan/odometry messages.
- Five training epochs and held-out evaluations for each of GRU, LSTM and
  Transformer on generated analytical trajectories; CV on identical test windows.
- Download and format inspection of the Social GAN authors' ETH/UCY archive.
- Pure model/data/metrics/geometry/replay tests and figure generation.

Full commands and outputs are in evidence logs and REPRODUCE.md. Launch wrapper
exit 124 denotes the deliberate timeout ending an otherwise persistent service.

## VERIFIED

Two packages build. Final colcon discovery executes **16 tests: zero failures,
errors or skips** (`evidence/colcon-test-retry.log`). Nine research-model/data/trial
unit tests passed before the training environment was removed; two additional
replay tests passed with system NumPy. These are 27 distinct unit tests, not 27
robot trials. The final isolated ROS probe passed fresh-command forwarding,
forecast-conflict stopping and stale-observation stopping, with track metadata.

Actual Gazebo sensing and commanded motion passed. SLAM created a new occupancy
grid and updated it while moving; map-to-odom was observed. AMCL loaded that map,
published poses and maintained TF. Two actual static-world Nav2 actions succeeded.
This does not validate AMCL recovery, map accuracy, collision freedom or dynamic
prediction-enabled navigation.

## MEASURED

| Observation | Saved executed measurement | Supporting file |
|---|---:|---|
| Direct-command wheel-odometry displacement | 0.596600 m | evidence/simulation-probe.json |
| Finite positive pixels in captured depth frame | 69,754 | evidence/simulation-probe.json |
| SLAM known cells, first to last recorded update | 1,517 → 30,252 | evidence/mapping/probe.json |
| Recorded SLAM map messages | 27 | evidence/mapping/probe.json |
| Saved SLAM source scans / odometry messages | 142 / 412 | evidence/mapping/probe.json |
| Initial A trial simulated duration | 4.055000 s | evidence/navigation/trial_A_initial.json |
| Initial A trial odometry path length | 0.873221 m | evidence/navigation/trial_A_initial.json |
| Isolated A trial simulated duration | 4.330000 s | evidence/navigation/trial_A.json |
| Isolated A trial odometry path length | 0.891321 m | evidence/navigation/trial_A.json |
| Structurally inspected archive text files | 98 | evidence/dataset-inspection.json |

Both A action statuses were 4 (succeeded). These are smoke trials, not a navigation
success-rate estimate. Depth pixels and map cells are counts, not accuracy scores.

Actual synthetic-only ADE/FDE/CPU latency and training histories are in
SYNTHETIC_RESULTS.md and evidence/final_synthetic_*/results.json, with genuine
checkpoints. Every neural model performed worse than CV on this short synthetic
fixture. No real-pedestrian prediction or navigation conclusion follows.

Collision rate, real-data ADE/FDE, detection AP/FPS, ground-truth localization
error, map accuracy and controlled predictive-navigation results:
**NOT EXECUTED — NO EXPERIMENTAL RESULT AVAILABLE.**

## FAILED

- First ros-base container creation exhausted disk; recovered with ros-core and
  staged installation. Exact Docker error is preserved in failures.md.
- Initial ROS build lacked Make/C/C++ compilers; fixed with build-essential;
  initial log retained in colcon-build.log.
- Initial final-check colcon test discovered zero tests and exited 5; fixed
  setup.py tests_require; rerun discovers and passes all 16. The failed log is
  retained in colcon-final.log.
- One root-level unittest invocation lacked PYTHONPATH and raised import errors;
  corrected invocation passed; failed log retained.
- Original ETH URL and guessed mirror path returned 404; the authors' actual
  archive link succeeded. Failed fetch logs retained.

No failed research trials are being concealed. No dynamic comparison trials ran.

## BLOCKED

Real-data training and recorded-data experimental replay await verified original
dataset permissions, coordinate units and time conventions. The downloaded
archive has no dataset license file; the code repository's MIT license is not
used as a substitute. Live detector execution/evaluation additionally needs
appropriate model weights, licensed detection data and the missing live RGB-D
pipeline. Available disk was about 8 GB; after measured training and saved
checkpoints, the training environment was removed to fit real SLAM/Nav2. PyTorch
must be reinstalled before further neural execution. The current ROS container
is retained as a session checkpoint; see pinned setup instructions to rebuild.

## NOT IMPLEMENTED

Live synchronized YOLO RGB-D ROS detections, observation-time TF conversion and
robust multi-person tracking; verified detection dataset acquisition/evaluation;
semantic pickup/delivery mission manager; ground-truth/contact collision recorder;
real-data resource-consumption benchmarking and full experimental orchestration.
Calibrated model uncertainty and safety-certified braking are unsupported.

Implemented but NOT EXECUTED: outdoor-world smoke test, runtime trajectory replay,
real-data training, B/C/D Nav2 trials, checkpoint inference inside the live ROS
predictor, and the combined Dockerfile build. AMCL recovery and quantitative
accuracy tests are also outstanding. All required A/B/C/D repeated dynamic
experiments remain unfinished.

## GITHUB COMMITS

- a01384f — custom Jazzy robot, forecast interfaces, models, tooling and tests.
- Evidence/documentation commit accompanies this report on
  `codex/robotics-research-20261112`; consult branch history for its final hash.

No changes have been merged into the repository default branch.
