# Gazebo + Nav2 integration

**Important:** This section is an integration recipe, not a verified end-to-end run.

Recommended configuration: Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic.

Nav2 official quickstart: https://ros-navigation.github.io/mkdocs.nav2.org/jazzy/getting_started/quickstart/quickstart/

After installing ROS 2:

    sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-nav2-minimal-tb*
    source /opt/ros/jazzy/setup.bash

Run the TurtleBot3 example according to the Nav2 quickstart. Check the actual installed topic names and message types:

    ros2 topic list
    ros2 topic info -v /cmd_vel
    ros2 topic info -v /scan
    ros2 topic info -v /odom

The safety gate **subscribes** to /cmd_vel_nav (geometry_msgs/Twist) and **publishes** to /cmd_vel (geometry_msgs/Twist). Remap Nav2's *final* velocity output (e.g. after the velocity smoother) to /cmd_vel_nav. There must be no second active publisher bypassing the supervisor to /cmd_vel. Nav2 may use TwistStamped in some configurations: adapt its output type before connecting.

Start project nodes with:

    ros2 launch delivery_robot demo.launch.py demo_people:=false

Supply /detected_people as a metric PoseArray **in odom**. Raw YOLO bounding boxes cannot be used directly: camera intrinsics, depth, extrinsics, synchronization and TF localization must be developed first. Set use_sim_time consistently for all nodes when running against Gazebo's /clock.

## Limitations

- The prototype carries future positions in a flattened PoseArray; it assumes exactly eight forecast samples per tracked person at 0.25 s spacing. A proper PredictedTrajectoryArray message should preserve track IDs, time offsets and uncertainty.
- The constant-velocity tracker is basic and can switch identities.
- The forward laser cone is not a complete robot footprint/swept-path check.
- A STOP command here is not equivalent to certified emergency braking.
- Real robot deployment requires independent hardware interlocks and risk assessment.
