#!/usr/bin/env python3
"""Record live SLAM evidence and save its actual occupancy grid and source scans."""
import json
import math
import time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener

rclpy.init();node=Node('mapping_evidence');buffer=Buffer();listener=TransformListener(buffer,node)
root=(Path(__file__).resolve().parents[1]/'evidence/mapping');root.mkdir(parents=True,exist_ok=True)
raw=(root/'source_observations.jsonl').open('w');maps=[];latest=[None];odom_count=[0];scan_count=[0]
def scan(m):
    scan_count[0]+=1
    raw.write(json.dumps(dict(topic='/scan',stamp=[m.header.stamp.sec,m.header.stamp.nanosec],frame=m.header.frame_id,
      angle_min=m.angle_min,angle_increment=m.angle_increment,range_min=m.range_min,range_max=m.range_max,
      ranges=[x if math.isfinite(x) else None for x in m.ranges]))+'\n')
def odom(m):
    odom_count[0]+=1;p=m.pose.pose.position;q=m.pose.pose.orientation
    raw.write(json.dumps(dict(topic='/odom',stamp=[m.header.stamp.sec,m.header.stamp.nanosec],
      frame=m.header.frame_id,child=m.child_frame_id,xy=[p.x,p.y],quaternion=[q.x,q.y,q.z,q.w]))+'\n')
def mapping(m):
    latest[0]=m
    maps.append(dict(width=m.info.width,height=m.info.height,known=sum(v>=0 for v in m.data),
      stamp=[m.header.stamp.sec,m.header.stamp.nanosec]))
subs=[node.create_subscription(LaserScan,'/scan',scan,qos_profile_sensor_data),
 node.create_subscription(Odometry,'/odom',odom,qos_profile_sensor_data),
 node.create_subscription(OccupancyGrid,'/map',mapping,QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))]
pub=node.create_publisher(Twist,'/cmd_vel',10);start=time.monotonic();motion=None;tf_seen=False
try:
    while time.monotonic()-start<45:
        rclpy.spin_once(node,timeout_sec=.02)
        if latest[0] is not None and motion is None:motion=time.monotonic()
        c=Twist()
        if motion is not None:
            t=time.monotonic()-motion
            if t<5:c.linear.x=.25
            elif t<8:c.angular.z=.5
            elif t<11:c.linear.x=.2
            elif t>13:break
        pub.publish(c)
        try:
            buffer.lookup_transform('map','odom',rclpy.time.Time());tf_seen=True
        except Exception:pass
    for _ in range(5):pub.publish(Twist());rclpy.spin_once(node,timeout_sec=.02)
    m=latest[0]
    passed=m is not None and len(maps)>1 and scan_count[0]>0 and odom_count[0]>0 and tf_seen
    changed=len({(x['width'],x['height'],x['known']) for x in maps})>1
    record=dict(kind='SLAM Toolbox on live simulated LiDAR and wheel odometry; no input map',
      passed=passed and changed,map_updates=maps,scan_messages=scan_count[0],odom_messages=odom_count[0],
      map_to_odom_observed=tf_seen,map_changed_during_motion=changed)
    if m is not None:
        o=m.info.origin;q=o.orientation;yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
        pixels=bytearray()
        for y in reversed(range(m.info.height)):
            for x in range(m.info.width):
                v=m.data[y*m.info.width+x];pixels.append(205 if v<0 else 254 if v<25 else 0 if v>65 else 205)
        (root/'indoor.pgm').write_bytes(f'P5\n{m.info.width} {m.info.height}\n255\n'.encode()+pixels)
        (root/'indoor.yaml').write_text(f'image: indoor.pgm\nmode: trinary\nresolution: {m.info.resolution}\norigin: [{o.position.x}, {o.position.y}, {yaw}]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.25\n')
        (root/'occupancy.json').write_text(json.dumps(dict(width=m.info.width,height=m.info.height,
          resolution=m.info.resolution,origin=[o.position.x,o.position.y,yaw],data=list(m.data))))
    (root/'probe.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
    if not record['passed']:raise SystemExit(1)
finally:
    raw.close();node.destroy_node();rclpy.shutdown()
