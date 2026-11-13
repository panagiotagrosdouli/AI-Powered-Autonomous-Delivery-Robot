#!/usr/bin/env python3
"""Offline YOLO RGB-D inference. Requires aligned depth in metres and calibrated K.
No performance claims are emitted; predictions are saved with source provenance.
Install ultralytics/opencv-python separately after reviewing model/dataset licenses.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from delivery_robot.perception import deproject, transform_point

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--rgb',type=Path,required=True);p.add_argument('--depth-m',type=Path,required=True)
    p.add_argument('--calibration',type=Path,required=True);p.add_argument('--weights',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    import cv2
    from ultralytics import YOLO
    image=cv2.imread(str(a.rgb));depth=np.load(a.depth_m)
    if image is None or depth.shape != image.shape[:2]: raise ValueError('Aligned RGB and depth required')
    c=json.loads(a.calibration.read_text());model=YOLO(a.weights)
    people=[]
    for result in model(image,classes=[0],verbose=False):
        for box in result.boxes:
            x1,y1,x2,y2=box.xyxy[0].cpu().tolist()
            # Torso centre; reject holes rather than invent metric distance.
            u=int((x1+x2)/2);v=int((y1+y2)/2)
            patch=depth[max(0,v-2):v+3,max(0,u-2):u+3]
            good=patch[np.isfinite(patch)&(patch>0)]
            if len(good)<5:continue
            point=deproject(u,v,float(np.median(good)),**c['intrinsics'])
            world=transform_point(point,c['translation'],c['quaternion_xyzw'])
            people.append(dict(position_m=world,confidence=float(box.conf[0]),bbox_xyxy=[x1,y1,x2,y2]))
    a.output.write_text(json.dumps(dict(frame_id=c['frame_id'],timestamp=c['timestamp'],
      rgb_sha256=hashlib.sha256(a.rgb.read_bytes()).hexdigest(),
      depth_sha256=hashlib.sha256(a.depth_m.read_bytes()).hexdigest(),people=people),indent=2))
if __name__=='__main__':main()
