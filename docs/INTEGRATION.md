# Integration contracts

`delivery_interfaces/PredictedTracks` has an odom-frame forecast-origin header,
a separate last detector observation time, and per-track IDs, observation times,
variable duration offsets and metric points. CV provides no calibrated uncertainty.
No image coordinates are accepted as metric detections.

Predictor validates frame, finite coordinates and monotonically advancing source
timestamps. Supervisor uses source sensor stamps and observation age rather than
refreshing freshness on each forecast publication. Commands time out after 0.5 s;
scan, odometry and detector/forecast data after 0.6 s. Clock resets fail closed and
require restarting stateful nodes. Scan and odometry subscriptions accept
best-effort sensor data. Pose quaternions and expected frames are validated.

Full-scan radial clearance is conservative for the robot's circular bounding
footprint; current code stops below 0.65 m and scales velocity until 1.25 m.
It rejects nonfinite inputs and commands above 0.5 m/s or 1 rad/s. A minimum
finite scan return is required, so an all-infinite scan stops the robot.
These are research defaults, not measured safe stopping limits. Sampled forecast
collision checking does not prove continuous-time clearance or account for
braking dynamics and uncertainty. Tracking is greedy and can switch identities.

Nav2 routing in navigation.launch.py:

- Controller/recovery output -> /cmd_vel_raw -> velocity smoother.
- A: smoother -> /cmd_vel -> Gazebo.
- B/C/D: smoother -> /cmd_vel_nav -> supervisor -> /cmd_vel -> Gazebo.
- B uses scan gating; C adds CV forecasts; D selects a verified checkpoint.

The real ROS transport test passed with synthetic detector messages, including
prediction-conflict stopping and stale-observation stopping. This is not live
YOLO evidence. Only A completed a Gazebo navigation trial. B/C/D end-to-end
navigation and trained-model ROS execution remain unverified.

The simulation uses /clock consistently. RGB/depth frame IDs are optical-frame
IDs; metric deprojection and unit-quaternion transforms have unit tests. Camera
calibration, depth alignment, time synchronization, multi-object tracking from
real detections and TF lookup at observation time are still needed for live vision.
