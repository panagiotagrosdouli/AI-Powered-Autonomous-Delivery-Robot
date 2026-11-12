# Reproduction

## Platform and dependencies

Target Ubuntu 24.04, ROS 2 Jazzy and Gazebo Harmonic. Official installation:
https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html

The executed environment was Debian 13 running the official `ros:jazzy-ros-core`
Ubuntu image, with official ROS apt packages. Image digest and installation logs
are preserved under evidence. The full Dockerfile is provided but its combined
image build was NOT EXECUTED. Allocate ample disk space (16 GB is a recommendation,
not a measured minimum). This executor exposed roughly 8 GB and required staged
package installation and removal of the training virtual environment.

On a configured Jazzy host:

```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-colcon-common-extensions python3-pytest \
 ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge ros-jazzy-xacro \
 ros-jazzy-robot-state-publisher ros-jazzy-slam-toolbox \
 ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
 ros-jazzy-dwb-core ros-jazzy-dwb-critics ros-jazzy-dwb-plugins
source /opt/ros/jazzy/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
cd ..
```

The original `scripts/install_ros_stack.sh` is retained for the upstream TurtleBot
runbook. The commands above are for this custom platform.

## Simulation and new mapping

Each command below runs from the repository root in a sourced terminal. Use
`LIBGL_ALWAYS_SOFTWARE=1` for the tested headless CPU-rendering configuration.

```bash
LIBGL_ALWAYS_SOFTWARE=1 ros2 launch delivery_robot simulation.launch.py
# Separate terminal:
ros2 launch delivery_robot mapping.launch.py
# Separate terminal (actively drives robot; no Nav2 process should be running):
python3 scripts/test_mapping.py
```

The probe records timestamped simulated scans/odometry and saves actual generated
occupancy data, `evidence/mapping/indoor.pgm`, and `indoor.yaml`. It overwrites its
output paths: copy existing evidence before a repeated trial. It requires map
updates, changing known-map information and map-to-odom TF, not just a loaded map.
It does not establish map geometric accuracy or loop-closure robustness.

For a direct sensor/motion smoke test instead of mapping:

```bash
python3 scripts/test_simulation.py
```

## Localization and navigation

Stop all mapping and simulator processes first. Restart the simulator, then:

```bash
ros2 launch delivery_robot navigation.launch.py \
 map:="$(pwd)/evidence/mapping/indoor.yaml" condition:=A
# Separate terminal:
python3 scripts/test_navigation.py
```

The AMCL initial pose is configured at the simulator origin. The probe initializes
pose again and sends a real NavigateToPose action to `(1,0)` in map. It preserves
failure records. Navigation commands pass through the velocity smoother.

A uses Nav2 directly. B adds full-scan reactive gating. C additionally requires
metric `/detected_people` in odom and uses constant velocity. D requires a verified
trained checkpoint and the Python research package plus PyTorch available in the
ROS interpreter. D refuses synthetic checkpoints by default. B/C/D navigation
trials have not executed; the topic routing is implemented, not validated end to end.
Never start another supervisor or teleop publisher on `/cmd_vel` during navigation.

## Models and datasets

```bash
python3 -m venv work/training-env
work/training-env/bin/pip install numpy==2.5.4 torch==2.5.1 \
 --index-url https://download.pytorch.org/whl/cpu
work/training-env/bin/python -m research.synthetic_fixture work/synthetic
for model in gru lstm transformer; do
 work/training-env/bin/python -m research.train --manifest work/synthetic/manifest.json \
  --kind "$model" --epochs 5 --output "work/synthetic_$model"
done
```

These train actual networks, but exclusively test the software. Source data_kind
must remain SYNTHETIC. Saved final checkpoints and metrics from this session are
in `evidence/final_synthetic_*`. CV is evaluated on the same held-out windows.

```bash
python scripts/fetch_trajectory_archive.py --directory work/datasets \
 --record work/dataset-inspection.json
```

This downloader checks format and records hashes; it DOES NOT grant permission.
No archive is redistributed. Verify original ETH/UCY terms, coordinate conventions
and seconds per frame before constructing a training manifest. The manifest must
specify source, data_kind, units=metres, license_verified, license information,
sample_interval_seconds, frame_stride, and train/val/test file lists with path,
scene_id and SHA256. Whole recording scene IDs must be disjoint between splits.
Do not split overlapping windows randomly. Source labels are declarations, not
an automatic legal or scientific verification system.

## Optional inference and replay

`pip install -e '.[vision]'` installs optional offline detection dependencies;
review Ultralytics/model terms separately. `scripts/detect_rgbd.py` requires a real
RGB image, aligned metric depth NumPy array, model weights, and a JSON calibration
with fx/fy/cx/cy, translation, quaternion_xyzw, frame_id and timestamp. Depth
alignment, calibrated extrinsics and timestamp correctness are operator obligations;
this offline utility does not synchronize or publish a live camera pipeline.

```bash
python -m research.replay work/source.txt work/tracks.json \
 --frame-seconds 0.04 --data-kind real-recorded --origin 0 0 --yaw 0
PYTHONPATH=. python3 scripts/replay_gazebo.py work/tracks.json --log work/replay.jsonl
```

0.04 here is an example argument, NOT verified dataset metadata. Supply the
source recording's actual seconds per raw frame index. This preserves irregular
source times and interpolates only inside recorded lifetimes. The world needs
Gazebo's user-commands plugin. These runtime replay commands have NOT EXECUTED.
No synthetic replay is evidence of real trajectory evaluation. Blocking service
calls can lag the simulation clock, and the log records actual processed times.

## Tests and figures

```bash
PYTHONPATH=ros2_ws/src/delivery_robot python -m unittest discover -s ros2_ws/src/delivery_robot/test -v
# Requires training dependencies:
PYTHONPATH=ros2_ws/src/delivery_robot python -m unittest discover -s tests -v
ROS_DOMAIN_ID=77 python3 scripts/test_ros_transport.py
cd ros2_ws && colcon test && colcon test-result --verbose
# With matplotlib installed, from repository root:
python scripts/generate_figures.py
```

The transport probe defaults to isolated domain 77; never share it with a robot.
GitHub Actions build ROS packages, exercise transport and run CPU model tests;
CI execution status must be checked separately from the local logs. Simulator
commands here were run with finite harness timeouts; exit 124 in launch wrappers
means the harness stopped an intentionally persistent process.
