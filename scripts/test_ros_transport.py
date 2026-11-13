#!/usr/bin/env python3
"""Executed ROS transport test; no simulator/navigation claims."""
import os
os.environ.setdefault("ROS_DOMAIN_ID", "77")
import json
import math
import time
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Pose, PoseArray, Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from delivery_interfaces.msg import PredictedTracks
from delivery_robot.nodes import Predictor, Supervisor

rclpy.init()
predictor, supervisor, driver = Predictor(), Supervisor(), Node('transport_test_driver')
executor=SingleThreadedExecutor()
for n in (predictor,supervisor,driver):executor.add_node(n)
people=driver.create_publisher(PoseArray,'/detected_people',10)
command=driver.create_publisher(Twist,'/cmd_vel_nav',10)
scan=driver.create_publisher(LaserScan,'/scan',qos_profile_sensor_data)
odom=driver.create_publisher(Odometry,'/odom',qos_profile_sensor_data)
outputs=[];forecasts=[]
sub=driver.create_subscription(Twist,'/cmd_vel',lambda m:outputs.append((time.monotonic(),m.linear.x)),10)
predsub=driver.create_subscription(PredictedTracks,'/predicted_people',lambda m:forecasts.append(m),10)
start=time.monotonic()
try:
    while time.monotonic()-start < 4.5:
        elapsed=time.monotonic()-start
        stamp=driver.get_clock().now().to_msg()
        s=LaserScan();s.header.stamp=stamp;s.header.frame_id='laser';s.angle_min=-.2;s.angle_increment=.1
        s.range_min=.1;s.range_max=10.;s.ranges=[2.]*5;scan.publish(s)
        o=Odometry();o.header.stamp=stamp;o.header.frame_id='odom';o.child_frame_id='base_link';o.pose.pose.orientation.w=1.;odom.publish(o)
        c=Twist();c.linear.x=.3;command.publish(c)
        if elapsed < 2.7:
            p=PoseArray();p.header.stamp=stamp;p.header.frame_id='odom'
            if elapsed >= 1.5:
                person=Pose();person.position.x=1.;person.orientation.w=1.;p.poses.append(person)
            people.publish(p)
        executor.spin_once(timeout_sec=.02)
        # Drain ready callbacks without blocking.
        for _ in range(8):executor.spin_once(timeout_sec=0)
        time.sleep(.02)
    moving=[v for t,v in outputs if 1.0<t-start<1.4]
    stopped=[v for t,v in outputs if t-start>3.8]
    assert moving and any(v>.25 for v in moving), 'No command passed with fresh best-effort sensor messages'
    conflicted=[v for t,v in outputs if 2.2<t-start<2.6]
    assert conflicted and all(v==0 for v in conflicted), 'Predicted conflict did not stop motion'
    assert any(len(m.tracks)==1 and len(m.tracks[0].positions)==12 for m in forecasts), 'Track/horizon metadata missing'
    assert stopped and all(v==0 for v in stopped), 'Repeated predictions masked stale observations'
    assert forecasts, 'No custom-interface transport'
    print(json.dumps(dict(test='ROS transport, not Gazebo',passed=True,outputs=len(outputs),
       forecast_messages=len(forecasts),fresh_command_passed=True,prediction_conflict_stopped=True,stale_observation_stopped=True)))
finally:
    for n in (predictor,supervisor,driver):executor.remove_node(n);n.destroy_node()
    executor.shutdown();rclpy.shutdown()
