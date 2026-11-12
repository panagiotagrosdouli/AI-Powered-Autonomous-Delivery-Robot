# AI-Powered Autonomous Delivery Robot

**ROS 2 Jazzy research prototype** for predictive pedestrian-aware navigation.

This repository includes a working *software architecture*: ROS 2 nodes for synthetic moving pedestrians, constant-velocity trajectory prediction, and a conservative command safety gate. **Gazebo/Nav2 end-to-end execution has not yet been verified.** The optional camera detector is not connected to 3D tracking. This project is not a safety-certified controller.

## Architecture

    /detected_people (PoseArray, odom) -> predictor -> /predicted_people
    /cmd_vel_nav (Twist) ---------------------------+
    /scan (LaserScan) ------------------------------+-> supervisor -> /cmd_vel (Twist)
    /odom (Odometry) -------------------------------+

The ROS 2 predictor uses nearest-neighbor tracking and a constant-velocity baseline, not a trained neural network. The supervisor stops on stale/missing inputs, close frontal obstacles, or forecast trajectory conflicts.

## Target platform

Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic. Follow the official installation: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html

## Build

    source /opt/ros/jazzy/setup.bash
    sudo apt install python3-colcon-common-extensions
    cd ros2_ws
    colcon build --symlink-install
    source install/setup.bash

## Run

    ros2 launch delivery_robot demo.launch.py

In a second terminal, request a motion command:

    ros2 topic pub -r 5 /cmd_vel_nav geometry_msgs/msg/Twist "{linear: {x: 0.3}}"

Inspect `/predicted_people` and `/cmd_vel`. **The supervisor outputs zero unless /odom and /scan are present**, which is expected when no simulated robot is running.

Run pure algorithm unit tests without ROS:

    cd ros2_ws/src/delivery_robot
    python3 -m unittest discover -s test -v

See [integration guide](docs/INTEGRATION.md) and [experiment plan](docs/EXPERIMENTS.md).

## Planned research extensions

1. Real Gazebo simulation and Nav2 velocity-topic integration.
2. Calibrated RGB-D detections transformed to odom with TF.
3. Comparison of constant velocity, GRU and Transformer trajectory predictors.
4. Controlled studies of success rate, collision rate, clearance, latency, ADE and FDE.

No experimental performance metrics are claimed yet.

## Run live LiDAR SLAM in Gazebo

This project includes executable wrappers around **Nav2's upstream TurtleBot3 Gazebo simulator and SLAM Toolbox**, so the robot can generate a map from live simulated LiDAR/odometry (rather than displaying a prerecorded map):

    bash scripts/install_ros_stack.sh
    bash scripts/run_slam.sh

In another terminal:

    source /opt/ros/jazzy/setup.bash
    python3 scripts/check_slam.py

Save a map and relaunch with AMCL using the commands in [SLAM runbook](docs/SLAM_RUNBOOK.md). These are documented procedures, **not claims of an executed simulator run in this repository**.
