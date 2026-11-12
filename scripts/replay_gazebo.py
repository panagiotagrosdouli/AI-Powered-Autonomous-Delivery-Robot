#!/usr/bin/env python3
"""Replay prepared tracks on ROS simulation clock via Gazebo Transport services.
Requires running world user-commands plugin; creates static cylinder proxies.
Commands are blocking: lateness is recorded, never reported as exact real-time.
"""
import argparse
import json
import subprocess
import rclpy
from rclpy.node import Node
from rosgraph_msgs.msg import Clock
from research.replay import pose_at

p=argparse.ArgumentParser();p.add_argument('tracks');p.add_argument('--world',default='delivery_world')
p.add_argument('--log',required=True);a=p.parse_args();data=json.load(open(a.tracks))

def call(service,reqtype,request):
    result=subprocess.run(['gz','service','-s',f'/world/{a.world}/{service}',
      '--reqtype',reqtype,'--reptype','gz.msgs.Boolean','--timeout','1000','--req',request],
      capture_output=True,text=True,timeout=3)
    if result.returncode or 'data: true' not in result.stdout:
        raise RuntimeError(f'{service}: {result.returncode} {result.stdout} {result.stderr}')

for track in data['tracks']:
    name=track['name']
    sdf=f'<sdf version="1.9"><model name="{name}"><static>true</static><pose>0 0 -10 0 0 0</pose><link name="body"><collision name="c"><geometry><cylinder><radius>0.3</radius><length>1.7</length></cylinder></geometry></collision><visual name="v"><geometry><cylinder><radius>0.3</radius><length>1.7</length></cylinder></geometry></visual></link></model></sdf>'
    call('create','gz.msgs.EntityFactory','sdf: '+json.dumps(sdf))

rclpy.init();node=Node('recorded_trajectory_replay');clock=[None]
sub=node.create_subscription(Clock,'/clock',lambda m:clock.__setitem__(0,m.clock.sec+m.clock.nanosec/1e9),10)
start=None;last=-1.;log=open(a.log,'w')
try:
    while rclpy.ok():
        rclpy.spin_once(node,timeout_sec=.05)
        if clock[0] is None:continue
        if start is None:start=clock[0]
        t=clock[0]-start
        if t<last:raise RuntimeError('Simulation clock reset; replay must be restarted')
        if t-last<.04:continue
        last=t
        for track in data['tracks']:
            xy=pose_at(track['samples'],t);x,y=xy if xy else (0,0);z=.85 if xy else -10
            req=f'name: "{track["name"]}" position: {{x: {x} y: {y} z: {z}}}'
            call('set_pose','gz.msgs.Pose',req)
        log.write(json.dumps(dict(replay_time_s=t,clock_s=clock[0],proxies=len(data['tracks'])))+'\n');log.flush()
        if t>max(tr['samples'][-1]['t'] for tr in data['tracks']):break
finally:
    log.close();node.destroy_node();rclpy.shutdown()
