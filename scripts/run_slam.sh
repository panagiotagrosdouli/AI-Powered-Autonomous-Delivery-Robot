#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/jazzy/setup.bash
# Use the actual Nav2 TurtleBot3 Gazebo simulator, LiDAR odometry and SLAM Toolbox.
# Runs online map estimation; never substitute a prerecorded map for mapping.
exec ros2 launch nav2_bringup tb3_simulation_launch.py slam:=True headless:=False "$@"
