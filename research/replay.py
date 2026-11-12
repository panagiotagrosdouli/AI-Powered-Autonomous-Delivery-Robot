"""Convert recorded four-column trajectories to collision-bearing Gazebo proxies.
This reconstructs simulated cylinders, never real-world scenes or detector outputs.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np

def convert(file, frame_seconds, origin, yaw):
    rows=np.loadtxt(file,ndmin=2)
    if rows.shape[1]!=4 or not np.isfinite(rows).all() or frame_seconds<=0:
        raise ValueError('Finite frame,id,x,y and positive seconds per raw frame required')
    if len(np.unique(rows[:,:2],axis=0))!=len(rows):raise ValueError('Duplicate frame/track')
    first=rows[:,0].min();tracks=[]
    for pid in np.unique(rows[:,1]):
        seq=rows[rows[:,1]==pid];seq=seq[np.argsort(seq[:,0])]
        samples=[]
        for frame,_,x,y in seq:
            samples.append(dict(t=float((frame-first)*frame_seconds),
              x=float(origin[0]+math.cos(yaw)*x-math.sin(yaw)*y),
              y=float(origin[1]+math.sin(yaw)*x+math.cos(yaw)*y)))
        tracks.append(dict(name='pedestrian_'+str(int(pid)),samples=samples))
    return tracks

def pose_at(samples,t):
    # Outside recorded lifetime: no extrapolated pedestrians.
    if not samples[0]['t']<=t<=samples[-1]['t']:return None
    times=[s['t'] for s in samples];i=int(np.searchsorted(times,t,side='right'))
    if i==len(samples):return samples[-1]['x'],samples[-1]['y']
    a,b=samples[max(0,i-1)],samples[i];f=(t-a['t'])/(b['t']-a['t']) if b['t']>a['t'] else 0
    return a['x']+f*(b['x']-a['x']),a['y']+f*(b['y']-a['y'])

if __name__=='__main__':
    import hashlib
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--frame-seconds',type=float,required=True)
    p.add_argument('--data-kind',choices=['real-recorded','synthetic'],required=True)
    p.add_argument('--origin',nargs=2,type=float,default=[0,0]);p.add_argument('--yaw',type=float,default=0)
    a=p.parse_args();tracks=convert(a.source,a.frame_seconds,a.origin,a.yaw)
    a.output.write_text(json.dumps(dict(source_sha256=hashlib.sha256(a.source.read_bytes()).hexdigest(),
      source_kind=a.data_kind,rendering='synthetic cylinder proxies',
      frame_seconds=a.frame_seconds,origin=a.origin,yaw=a.yaw,tracks=tracks),indent=2))
