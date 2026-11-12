"""Geometry and association independent of ROS and detector weights."""
from math import isfinite

def deproject(u, v, depth_m, fx, fy, cx, cy):
    vals=(u,v,depth_m,fx,fy,cx,cy)
    if not all(isfinite(x) for x in vals) or depth_m <= 0 or fx <= 0 or fy <= 0:
        raise ValueError('Invalid calibrated depth sample')
    return ((u-cx)*depth_m/fx,(v-cy)*depth_m/fy,depth_m)

def transform_point(point, translation, quaternion):
    x,y,z,w=quaternion
    if not all(isfinite(v) for v in (*point,*translation,*quaternion)):
        raise ValueError('Nonfinite transform')
    if abs(x*x+y*y+z*z+w*w-1) > 1e-3:
        raise ValueError('Transform quaternion must be unit length')
    px,py,pz=point
    # Rotation q*p*q^-1, using the vector cross-product identity.
    tx,ty,tz=2*(y*pz-z*py),2*(z*px-x*pz),2*(x*py-y*px)
    return (px+w*tx+y*tz-z*ty+translation[0],
            py+w*ty+z*tx-x*tz+translation[1],
            pz+w*tz+x*ty-y*tx+translation[2])
