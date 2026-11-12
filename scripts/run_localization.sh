#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/run_localization.sh /absolute/path/to/saved_map.yaml" >&2
  exit 2
fi
MAP="$1"
shift
if [[ ! -f "$MAP" ]]; then
  echo "Missing map: $MAP" >&2
  exit 2
fi
source /opt/ros/jazzy/setup.bash
# Stock Nav2 mode: saved occupancy map + AMCL + navigation.
exec ros2 launch nav2_bringup tb3_simulation_launch.py slam:=False map:="$MAP" headless:=False "$@"
