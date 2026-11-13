> Historical upstream TurtleBot alternative. For the custom robot that actually executed in this session, follow [REPRODUCE.md](REPRODUCE.md). This upstream wrapper itself remains unexecuted.

# Real SLAM computation in Gazebo — reproducible runbook

This procedure uses **live simulated LiDAR and wheel odometry**, processed by the actual `slam_toolbox` package to generate a **new occupancy grid** and `map -> odom` transform. It is genuine algorithmic SLAM on simulated sensor observations, **not physical-world SLAM**. Physical-world SLAM requires a sensor-equipped robot.

## Prerequisites

Ubuntu 24.04 / ROS 2 Jazzy / Gazebo Harmonic. Follow official ROS 2 installation and then:

    bash scripts/install_ros_stack.sh

Verify installation of `nav2_bringup`, `slam_toolbox`, and `nav2_minimal_tb3_sim`.

## Mapping phase

Terminal 1 (from repository root):

    bash scripts/run_slam.sh

This invokes Nav2's official TurtleBot3 Gazebo launch with `slam:=True`, including SLAM Toolbox. A Gazebo sandbox and RViz should appear.

Explore the simulated space using Nav2 goals in RViz. Avoid publishing teleop commands concurrently with Nav2.

Terminal 2:

    source /opt/ros/jazzy/setup.bash
    python3 scripts/check_slam.py

A PASS means the monitor observed finite LiDAR ranges, odometry, an occupied/known map and `map -> odom` TF. A PASS **does not** prove map geometric accuracy or loop-closure quality.

While robot is exploring, watch the occupancy grid expand in RViz. Save the live generated map:

    mkdir -p maps
    ros2 run nav2_map_server map_saver_cli -f "$(pwd)/maps/mapped_world"

This should create `maps/mapped_world.yaml` and an image file. Do not commit maps or benchmark outcomes without provenance.

## Localization and navigation phase

Stop the SLAM launch before switching modes (do not leave two simulation stacks active):

    bash scripts/run_localization.sh "$(pwd)/maps/mapped_world.yaml"

This starts an AMCL-based localization setup with the map you saved. Set initial pose using RViz's **2D Pose Estimate**, then send a **Nav2 Goal**. Confirm the robot moves to the goal.

## Evidence to capture

- `ros2 topic info /scan`, `/odom`, `/map`
- `ros2 run tf2_ros tf2_echo map odom`
- A screenshot of a live expanding map while exploring
- The saved map and exact map resolution
- One Nav2 goal with start, target, outcome and completion time
- Known software versions and output of check_slam.py

No empirical results are claimed until these commands execute on a working ROS 2 host.

## Known limitations and next research tasks

The stock TurtleBot3 sandbox is not a custom delivery platform. The current `delivery_robot` safety node is not automatically wired to Nav2. The simulated world does not yet include dataset-driven pedestrians. These are separate engineering milestones.
