"""Calibrated rectified, registered RGB-D geometry and explicit detector adapters."""
import numpy as np
from .perception import deproject,transform_point

def calibrated_intrinsics(info,width,height):
    if (info.width,info.height)!=(width,height) or info.binning_x>1 or info.binning_y>1:
        raise ValueError('Calibration resolution/binning mismatch')
    if info.roi.x_offset or info.roi.y_offset or info.roi.width not in (0,width) or info.roi.height not in (0,height):
        raise ValueError('Unsupported calibration ROI')
    if any(abs(d)>1e-9 for d in info.d):raise ValueError('Rectified zero-distortion images required')
    k=np.asarray(info.k).reshape(3,3)
    if not np.isfinite(k).all() or k[0,0]<=0 or k[1,1]<=0 or abs(k[2,2]-1)>1e-6 or abs(k[0,1])>1e-9:
        raise ValueError('Invalid pinhole calibration')
    return dict(fx=float(k[0,0]),fy=float(k[1,1]),cx=float(k[0,2]),cy=float(k[1,2]))

def metric_observations(rgb,depth,boxes,intrinsics,translation,quaternion):
    if depth.shape!=rgb.shape[:2]:raise ValueError('Registered depth resolution mismatch')
    observations=[]
    for x1,y1,x2,y2,confidence in boxes:
        if not np.isfinite([x1,y1,x2,y2,confidence]).all():raise ValueError('Nonfinite detection')
        x1=max(0,int(x1));y1=max(0,int(y1));x2=min(rgb.shape[1],int(x2));y2=min(rgb.shape[0],int(y2))
        if x2-x1<4 or y2-y1<4:continue
        # Central torso patch avoids boundary/background depth; no depth imputation.
        u=(x1+x2)//2;v=y1+(y2-y1)//3
        rx=max(1,(x2-x1)//10);ry=max(1,(y2-y1)//12)
        patch=depth[max(y1,v-ry):min(y2,v+ry+1),max(x1,u-rx):min(x2,u+rx+1)]
        good=patch[np.isfinite(patch)&(patch>.1)&(patch<20)]
        if len(good)<5:continue
        z=float(np.median(good))
        # Reject depth discontinuities, rather than mixing foreground/background.
        if np.percentile(good,75)-np.percentile(good,25)>.5:continue
        optical=deproject(u,v,z,**intrinsics);world=transform_point(optical,translation,quaternion)
        crop=rgb[y1:y2,x1:x2];feature=[]
        for c in range(3):
            hist=np.histogram(crop[:,:,c],bins=8,range=(0,256))[0].astype(float)
            feature.extend((hist/max(hist.sum(),1)).tolist())
        observations.append((world[0],world[1],tuple(feature)))
    return observations

class HogDetector:
    """OpenCV's distributed default people SVM. No accuracy claim is implied."""
    def __init__(self):
        import cv2
        self.cv2=cv2;self.hog=cv2.HOGDescriptor();self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    def __call__(self,rgb):
        if rgb.shape[0]<128 or rgb.shape[1]<64:return []
        boxes,scores=self.hog.detectMultiScale(self.cv2.cvtColor(rgb,self.cv2.COLOR_RGB2BGR),
          winStride=(8,8),padding=(8,8),scale=1.05)
        return [(x,y,x+w,y+h,float(s)) for (x,y,w,h),s in zip(boxes,scores)]

class YoloOnnxDetector:
    """YOLOv8 detection ONNX [1,84,N], OpenCV DNN CPU; verified local weights only."""
    def __init__(self,manifest):
        import cv2,hashlib,json
        from pathlib import Path
        p=Path(manifest);meta=json.loads(p.read_text());weights=p.parent/meta['path']
        if meta.get('license_verified') is not True or hashlib.sha256(weights.read_bytes()).hexdigest()!=meta['sha256']:
            raise ValueError('Unverified detector weights/license/checksum')
        self.cv2=cv2;self.net=cv2.dnn.readNetFromONNX(str(weights));self.size=int(meta['input_size'])
        self.threshold=float(meta.get('confidence',.4));self.nms=float(meta.get('nms',.45))
    def __call__(self,rgb):
        cv=self.cv2;h,w=rgb.shape[:2];scale=min(self.size/w,self.size/h)
        nw,nh=round(w*scale),round(h*scale);left=(self.size-nw)//2;top=(self.size-nh)//2
        canvas=np.full((self.size,self.size,3),114,dtype=np.uint8)
        canvas[top:top+nh,left:left+nw]=cv.resize(rgb,(nw,nh))
        self.net.setInput(cv.dnn.blobFromImage(canvas,1/255.,(self.size,self.size),swapRB=False))
        out=self.net.forward()
        if out.ndim!=3 or out.shape[0]!=1 or out.shape[1]!=84:raise ValueError('Expected YOLOv8 COCO detection export [1,84,N]')
        boxes=[];scores=[]
        for row in out[0].T:
            if int(np.argmax(row[4:]))!=0 or row[4]<self.threshold:continue
            cx,cy,bw,bh=row[:4];boxes.append([float((cx-bw/2-left)/scale),float((cy-bh/2-top)/scale),float(bw/scale),float(bh/scale)])
            scores.append(float(row[4]))
        keep=cv.dnn.NMSBoxes(boxes,scores,self.threshold,self.nms)
        return [(boxes[int(i)][0],boxes[int(i)][1],boxes[int(i)][0]+boxes[int(i)][2],boxes[int(i)][1]+boxes[int(i)][3],scores[int(i)]) for i in np.asarray(keep).reshape(-1)]
