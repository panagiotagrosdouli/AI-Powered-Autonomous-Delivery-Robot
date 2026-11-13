#!/usr/bin/env python3
"""Capture actual live inference/TF/synchronization evidence; no invented boxes."""
import json,time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo
from std_msgs.msg import String
from delivery_interfaces.msg import TrackedPeople,PredictedTracks
rclpy.init();node=Node('live_perception_probe');records=[];people=[];forecasts=[];calibration=[]
subs=[node.create_subscription(String,'/perception/status',lambda m:records.append(json.loads(m.data)),10),
 node.create_subscription(TrackedPeople,'/tracked_people',lambda m:people.append(len(m.people)),10),
 node.create_subscription(PredictedTracks,'/predicted_people',lambda m:forecasts.append(len(m.tracks)),10),
 node.create_subscription(CameraInfo,'/camera/camera_info',lambda m:calibration.append(dict(k=list(m.k),d=list(m.d),width=m.width,height=m.height,frame=m.header.frame_id)),qos_profile_sensor_data)]
try:
 deadline=time.monotonic()+15
 while time.monotonic()<deadline:rclpy.spin_once(node,timeout_sec=.05)
 result=dict(kind='ACTUAL Gazebo camera -> OpenCV HOG -> registered depth -> observation-time TF -> tracker -> CV predictor',
  detector_status=records[-1] if records else None,track_messages=len(people),forecast_messages=len(forecasts),
  observed_track_counts=people,calibration=calibration[-1] if calibration else None,
  limitation='Indoor synthetic world has no human models; zero detections cannot validate pedestrian accuracy')
 result['passed']=bool(records and records[-1]['counts'].get('published',0)>10 and people and forecasts and calibration)
 root=Path(__file__).resolve().parents[1]/'evidence/phase2';(root/'live-perception-probe.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result,indent=2))
 if not result['passed']:raise SystemExit(1)
finally:node.destroy_node();rclpy.shutdown()
