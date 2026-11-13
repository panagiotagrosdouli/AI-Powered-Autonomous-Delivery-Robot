# Preserved failure and contamination notes

The first `docker run` with ros:jazzy-ros-base failed:

```
docker: Error response from daemon: mkdir /home/dockerd/.local/share/docker/vfs/dir/12e82bc309ac49045d04e247ff0d2bc74901f0e13994fc42bd7f3bce9565c0a9/usr/libexec/sudo: no space left on device
```

This is a captured tool error transcribed here, not generated terminal evidence.
The next sandbox command also failed because no temporary mount directory could
be created. Removing only the just-downloaded image recovered space. The smaller
ros-core image then ran successfully. Full-stack apt estimates were initially
larger than available space, so dependencies were installed in stages. The
training virtual environment was removed after successful model checks to fit
SLAM and a minimal Nav2 stack; this is recorded in torch-disk-recovery.log.

colcon-build.log records missing compiler tools, repaired before subsequent builds.
colcon-final.log records zero tests / exit 5, fixed via setup.py tests_require;
colcon-test-retry.log records actual 16 passing tests. The root unittest invocation
without PYTHONPATH is preserved as algorithm-tests-root-attempt.log.
Dataset original/mirror 404 attempts and actual authors' archive fetch are retained.

One earlier transport probe shared domain 0 with the running simulator after the
first A action had already completed. Its injected wall-stamped fixture sensors
caused later TF filter warnings in nav2-live.log. This shared-domain transport
attempt is NOT relied upon as isolated verification. The transport script now
defaults to isolated ROS domain 77, and its final predictive probe passed there.
A second clean A navigation smoke trial used ROS domain 89 and a separate Gazebo
partition. Both trial files are preserved; only logs from the clean run are used
for the final isolated integration checkpoint. No outcome is dropped.

Gazebo's gz_frame_id extension emits SDF warnings, but observed ROS sensor frame
IDs were laser and camera_optical_frame. KDL's root-link inertia warning does not
prevent kinematic TF publication. No geometric/dynamic accuracy is inferred from
these warnings. Figure generation emitted a font-cache warning but produced SVGs.

Harness timeouts (124) deliberately stop long-lived launch processes after tests;
they are not successful simulation-trial outcomes by themselves.
