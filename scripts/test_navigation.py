#!/usr/bin/env python3
"""Execute one real NavigateToPose action; preserve failures and odometry trace."""
import json
import math
import time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.action import ActionClient
from rclpy.qos import qos_profile_sensor_data
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseWithCovarianceStamped
from tf2_ros import Buffer,TransformListener

rclpy.init();node=Node('navigation_trial',parameter_overrides=[Parameter('use_sim_time',value=True)])
client=ActionClient(node,NavigateToPose,'navigate_to_pose');poses=[];amcl=[]
def odom(m):
 p=m.pose.pose.position;poses.append(dict(t=m.header.stamp.sec+m.header.stamp.nanosec/1e9,x=p.x,y=p.y))
subs=[node.create_subscription(Odometry,'/odom',odom,qos_profile_sensor_data),
 node.create_subscription(PoseWithCovarianceStamped,'/amcl_pose',lambda m:amcl.append(m),10)]
initial=node.create_publisher(PoseWithCovarianceStamped,'/initialpose',10)
buf=Buffer();listener=TransformListener(buf,node);result=dict(condition='A',kind='actual static-world Gazebo Nav2 trial',success=False)
start=time.monotonic()
def wait(future,seconds):
 deadline=time.monotonic()+seconds
 while not future.done() and time.monotonic()<deadline:rclpy.spin_once(node,timeout_sec=.05)
 if not future.done():raise TimeoutError('Action response timed out')
 return future.result()
try:
 if not client.wait_for_server(timeout_sec=30):raise TimeoutError('NavigateToPose action server unavailable')
 for _ in range(10):
  m=PoseWithCovarianceStamped();m.header.frame_id='map';m.header.stamp=node.get_clock().now().to_msg()
  m.pose.pose.orientation.w=1.;m.pose.covariance[0]=.05;m.pose.covariance[7]=.05;m.pose.covariance[35]=.05
  initial.publish(m);rclpy.spin_once(node,timeout_sec=.1)
 goal=NavigateToPose.Goal();goal.pose.header.frame_id='map';goal.pose.header.stamp=node.get_clock().now().to_msg()
 goal.pose.pose.position.x=1.;goal.pose.pose.orientation.w=1.
 request_t=node.get_clock().now().nanoseconds/1e9
 handle=wait(client.send_goal_async(goal),10)
 if not handle.accepted:raise RuntimeError('Navigation goal rejected')
 reply=wait(handle.get_result_async(),60)
 result.update(success=reply.status==4,action_status=reply.status,goal_map_xy=[1.,0.],
   simulated_navigation_time_s=node.get_clock().now().nanoseconds/1e9-request_t)
 try:
  transform=buf.lookup_transform('map','odom',rclpy.time.Time());result['map_to_odom_valid']=True
 except Exception:result['map_to_odom_valid']=False
 result['amcl_pose_messages']=len(amcl)
 result['odometry_path_length_m']=sum(math.hypot(b['x']-a['x'],b['y']-a['y']) for a,b in zip(poses,poses[1:]))
except Exception as error:result['failure']=str(error)
finally:
 result['wall_seconds']=time.monotonic()-start
 result['collision_rate']='NOT MEASURED; no contact instrumentation'
 root=(Path(__file__).resolve().parents[1]/'evidence/navigation');root.mkdir(parents=True,exist_ok=True)
 (root/'trial_A.json').write_text(json.dumps(result,indent=2));(root/'odom_path.json').write_text(json.dumps(poses))
 print(json.dumps(result,indent=2));node.destroy_node();rclpy.shutdown()
if not result['success']:raise SystemExit(1)
