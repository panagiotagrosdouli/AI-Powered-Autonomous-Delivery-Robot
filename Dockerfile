FROM ros:jazzy-ros-base
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
 build-essential python3-colcon-common-extensions python3-pytest \
 ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge ros-jazzy-robot-state-publisher \
 ros-jazzy-xacro ros-jazzy-slam-toolbox ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /project
COPY . .
RUN . /opt/ros/jazzy/setup.sh && cd ros2_ws && colcon build --symlink-install
CMD ["bash"]
