#!/usr/bin/env python3
"""ROS integration with explicit injected boxes; NOT detector-performance evidence."""
import os
os.environ.setdefault('ROS_DOMAIN_ID','78')
import json
import time
from pathlib import Path
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from builtin_interfaces.msg import Time
from sensor_msgs.msg import Image,CameraInfo
from geometry_msgs.msg import TransformStamped
from tf2_msgs.msg import TFMessage
from cv_bridge import CvBridge
from delivery_interfaces.msg import TrackedPeople
from delivery_robot.live_perception import RGBDPerception

rclpy.init()
node=RGBDPerception(detector=lambda _: [(80,20,120,140,.99)],parameter_overrides=[
 Parameter('registered_rectified_depth',value=True)])
driver=Node('rgbd_fixture_driver');executor=SingleThreadedExecutor()
for n in (node,driver):executor.add_node(n)
bridge=CvBridge();outputs=[]
pubs=[driver.create_publisher(t,topic,qos_profile_sensor_data) for t,topic in
 [(Image,'/camera/image'),(Image,'/camera/depth_image'),(CameraInfo,'/camera/camera_info')]]
tfpub=driver.create_publisher(TFMessage,'/tf',10)
sub=driver.create_subscription(TrackedPeople,'/tracked_people',outputs.append,10)
def stamp(t):
 ns=int(t*1e9);return Time(sec=ns//1000000000,nanosec=ns%1000000000)
def fixture(t,frame='camera_optical_frame',distortion=False):
 rgb=bridge.cv2_to_imgmsg(np.full((160,200,3),120,dtype=np.uint8),'rgb8');rgb.header.stamp=stamp(t);rgb.header.frame_id=frame
 depth=bridge.cv2_to_imgmsg(np.full((160,200),2.,dtype=np.float32),'32FC1');depth.header.stamp=stamp(t+.01);depth.header.frame_id=frame
 info=CameraInfo(width=200,height=160,k=[100.,0.,100.,0.,100.,80.,0.,0.,1.]);info.header.frame_id=frame;info.header.stamp=stamp(t+.005)
 if distortion:info.d=[.1,0.,0.,0.,0.]
 for p,m in zip(pubs,(rgb,depth,info)):p.publish(m)
def tf(t,x):
 m=TransformStamped();m.header.stamp=stamp(t);m.header.frame_id='odom';m.child_frame_id='camera_optical_frame'
 m.transform.translation.x=x;m.transform.rotation.x=-.5;m.transform.rotation.y=.5;m.transform.rotation.z=-.5;m.transform.rotation.w=.5
 return m
try:
 # Wait for DDS discovery without assuming a fixed publisher startup order.
 deadline=time.monotonic()+2
 while time.monotonic()<deadline:executor.spin_once(timeout_sec=.02)
 observation=driver.get_clock().now().nanoseconds/1e9-.15
 tfpub.publish(TFMessage(transforms=[tf(observation,1.),tf(observation+.1,9.)]))
 fixture(observation)
 deadline=time.monotonic()+.3
 while time.monotonic()<deadline:executor.spin_once(timeout_sec=.005)
 assert outputs and len(outputs[-1].people)==1,'No synchronized metric track'
 person=outputs[-1].people[0]
 assert abs(person.position.x-3.)<1e-5,'Latest TF was incorrectly used instead of observation-time TF'
 assert abs(person.position.y)<1e-5
 assert abs((person.observed_at.sec+person.observed_at.nanosec/1e9)-observation)<1e-6
 count=len(outputs)
 # Missing TF must never masquerade as an empty, healthy detector observation.
 fixture(driver.get_clock().now().nanoseconds/1e9-.05,frame='unknown_camera')
 deadline=time.monotonic()+.65
 while time.monotonic()<deadline:executor.spin_once(timeout_sec=.01)
 assert len(outputs)==count,'TF failure emitted a false healthy observation'
 assert node.counts['stale_rejected']>0
 # Distortion/calibration rejection and stale timestamps.
 t=driver.get_clock().now().nanoseconds/1e9-.05
 tfpub.publish(TFMessage(transforms=[tf(t,1.)]));fixture(t,distortion=True)
 deadline=time.monotonic()+.15
 while time.monotonic()<deadline:executor.spin_once(timeout_sec=.01)
 assert node.counts['invalid_frame']>0
 fixture(driver.get_clock().now().nanoseconds/1e9-2)
 deadline=time.monotonic()+.1
 while time.monotonic()<deadline:executor.spin_once(timeout_sec=.01)
 assert len(outputs)==count
 result=dict(kind='SYNTHETIC ROS integration; injected bounding box; no detector accuracy evidence',
   passed=True,observation_time_tf_x_m=person.position.x,persistent_id=person.track_id,counts=dict(node.counts))
 print(json.dumps(result,indent=2))
finally:
 for n in (node,driver):executor.remove_node(n);n.destroy_node()
 executor.shutdown();rclpy.shutdown()
