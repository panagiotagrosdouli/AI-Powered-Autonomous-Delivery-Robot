"""Velocity-predicted global assignment with optional appearance and bounded occlusion.
No tracker can guarantee identity under indistinguishable full occlusion.
"""
from dataclasses import dataclass
from math import hypot, isfinite


def assignment(cost):
    """Rectangular Hungarian assignment, rows <= columns, finite costs."""
    n=len(cost)
    if not n:return []
    m=len(cost[0])
    if m<n or any(len(r)!=m or not all(isfinite(x) for x in r) for r in cost):
        raise ValueError('Invalid assignment matrix')
    u=[0.]*(n+1);v=[0.]*(m+1);p=[0]*(m+1);way=[0]*(m+1)
    for i in range(1,n+1):
        p[0]=i;j0=0;minimum=[float('inf')]*(m+1);used=[False]*(m+1)
        while True:
            used[j0]=True;i0=p[j0];delta=float('inf');j1=0
            for j in range(1,m+1):
                if not used[j]:
                    cur=cost[i0-1][j-1]-u[i0]-v[j]
                    if cur<minimum[j]:minimum[j]=cur;way[j]=j0
                    if minimum[j]<delta:delta=minimum[j];j1=j
            for j in range(m+1):
                if used[j]:u[p[j]]+=delta;v[j]-=delta
                else:minimum[j]-=delta
            j0=j1
            if p[j0]==0:break
        while True:
            j1=way[j0];p[j0]=p[j1];j0=j1
            if j0==0:break
    return [(p[j]-1,j-1) for j in range(1,m+1) if p[j]]

@dataclass
class PersonTrack:
    x: float
    y: float
    vx: float
    vy: float
    stamp: float
    appearance: tuple = ()
    hits: int = 1

class MultiPersonTracker:
    def __init__(self,gate=.8,max_age=.6,appearance_weight=.4):
        self.gate=gate;self.max_age=max_age;self.appearance_weight=appearance_weight
        self.tracks={};self.next_id=1;self.last_stamp=None

    def update(self,observations,stamp):
        # observations: (x_m,y_m,normalized appearance tuple)
        if not isfinite(stamp) or self.last_stamp is not None and stamp<=self.last_stamp:
            raise ValueError('Nonmonotonic observation time')
        if any(not all(isfinite(x) for x in (o[0],o[1],*o[2])) for o in observations):
            raise ValueError('Nonfinite observation')
        self.last_stamp=stamp
        self.tracks={i:t for i,t in self.tracks.items() if 0<=stamp-t.stamp<=self.max_age}
        ids=list(self.tracks);cost=[]
        for i in ids:
            t=self.tracks[i];dt=stamp-t.stamp;row=[]
            for x,y,feature in observations:
                distance=hypot(x-(t.x+t.vx*dt),y-(t.y+t.vy*dt))
                appearance=sum(abs(a-b) for a,b in zip(feature,t.appearance)) if len(feature)==len(t.appearance) else 0
                row.append(distance+self.appearance_weight*appearance if distance<=self.gate else 1e6)
            # Unmatched is cheaper than a gated or implausible association.
            row.extend([self.gate+self.appearance_weight]*len(ids));cost.append(row)
        used=set()
        for i,j in assignment(cost):
            if j>=len(observations) or cost[i][j]>=self.gate+self.appearance_weight:continue
            t=self.tracks[ids[i]];x,y,feature=observations[j];dt=stamp-t.stamp
            t.vx=(x-t.x)/dt;t.vy=(y-t.y)/dt;t.x=x;t.y=y;t.stamp=stamp
            t.appearance=tuple(feature);t.hits+=1;used.add(j)
        for j,(x,y,feature) in enumerate(observations):
            if j not in used:
                self.tracks[self.next_id]=PersonTrack(x,y,0.,0.,stamp,tuple(feature));self.next_id+=1
        return self.tracks
