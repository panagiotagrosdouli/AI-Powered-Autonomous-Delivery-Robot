#!/usr/bin/env bash
set -euo pipefail
if [[ "$(lsb_release -rs)" != "24.04" ]]; then
  echo "Expected Ubuntu 24.04; found $(lsb_release -rs)" >&2
  exit 2
fi
if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo "Install ROS 2 Jazzy first: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html" >&2
  exit 2
fi
sudo apt-get update
sudo apt-get install -y \
  python3-colcon-common-extensions \
  ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-nav2-minimal-tb3 ros-jazzy-slam-toolbox \
  ros-jazzy-nav2-map-server ros-jazzy-teleop-twist-keyboard
source /opt/ros/jazzy/setup.bash
cd "$(dirname "$0")/../ros2_ws"
colcon build --symlink-install
echo "Installation/build completed. Source install/setup.bash."
