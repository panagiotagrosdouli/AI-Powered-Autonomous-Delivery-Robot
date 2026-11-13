#!/usr/bin/env python3
"""Actual simulated sensor/motion probe; publishes direct test commands, no Nav2."""
import json
import math
import struct
import time
import zlib
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan, Image

rclpy.init();node=Node('simulation_probe')
seen={'scan':0,'odom':0,'rgb':0,'depth':0};positions=[];last_scan=[];frames={};stamps={}
def scan(m):
    good=[x for x in m.ranges if math.isfinite(x) and m.range_min<=x<=m.range_max]
    if good:seen['scan']+=1;last_scan[:]=good;stamps['scan']=m.header.frame_id
def odom(m):
    p=m.pose.pose.position
    if all(math.isfinite(v) for v in (p.x,p.y,p.z)):
        seen['odom']+=1;positions.append((time.monotonic(),p.x,p.y));stamps['odom']=[m.header.frame_id,m.child_frame_id]
def image(m,key):
    if m.width>0 and m.height>0 and m.data:
        seen[key]+=1;frames[key]=m;stamps[key]=m.header.frame_id
subs=[node.create_subscription(LaserScan,'/scan',scan,qos_profile_sensor_data),
      node.create_subscription(Odometry,'/odom',odom,qos_profile_sensor_data),
      node.create_subscription(Image,'/camera/image',lambda m:image(m,'rgb'),qos_profile_sensor_data),
      node.create_subscription(Image,'/camera/depth_image',lambda m:image(m,'depth'),qos_profile_sensor_data)]
pub=node.create_publisher(Twist,'/cmd_vel',10);start=time.monotonic();motion_start=None;initial=None;final=None
try:
    while time.monotonic()-start<40:
        rclpy.spin_once(node,timeout_sec=.05)
        if all(seen.values()) and motion_start is None:
            motion_start=time.monotonic();initial=positions[-1][1:]
        command=Twist()
        if motion_start is not None:
            elapsed=time.monotonic()-motion_start
            if elapsed<3:command.linear.x=.2
            if elapsed>4:
                final=positions[-1][1:];break
        pub.publish(command)
    for _ in range(5):pub.publish(Twist());rclpy.spin_once(node,timeout_sec=.02)
    displacement=math.dist(initial,final) if initial is not None and final is not None else None
    result=dict(kind='ACTUAL GAZEBO SIMULATION; direct motion test, not autonomous navigation',
      messages=seen,frames=stamps,initial_odom_xy=initial,final_odom_xy=final,
      odometry_displacement_m=displacement,min_finite_scan_range_m=min(last_scan) if last_scan else None,
      passed=all(seen.values()) and displacement is not None and displacement>.2)
    if 'depth' in frames:
        depth=frames['depth'];result['depth_encoding']=depth.encoding
        if depth.encoding=='32FC1':
            vals=[v[0] for v in struct.iter_unpack('>f' if depth.is_bigendian else '<f',bytes(depth.data))]
            valid=[v for v in vals if math.isfinite(v) and v>0]
            result['finite_positive_depth_pixels']=len(valid)
            result['passed']=result['passed'] and len(valid)>0
    (Path(__file__).resolve().parents[1]/'evidence/simulation-probe.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if 'rgb' in frames:
        m=frames['rgb']
        if m.encoding=='rgb8':
            raw=b''.join(b'\0'+bytes(m.data[y*m.step:y*m.step+m.width*3]) for y in range(m.height))
            def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
            png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',m.width,m.height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
            (Path(__file__).resolve().parents[1]/'evidence/simulated-camera-frame.png').write_bytes(png)
    if not result['passed']:raise SystemExit(1)
finally:
    node.destroy_node();rclpy.shutdown()
