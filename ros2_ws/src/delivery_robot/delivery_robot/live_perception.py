"""Synchronized registered RGB-D -> observation-time TF -> persistent metric tracks."""
from collections import Counter
import json
import time
import numpy as np
import message_filters
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.time import Time
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
from sensor_msgs.msg import Image,CameraInfo
from std_msgs.msg import String
from tf2_ros import Buffer,TransformListener,TransformException
from delivery_interfaces.msg import TrackedPerson,TrackedPeople
from .rgbd import HogDetector,YoloOnnxDetector,calibrated_intrinsics,metric_observations
from .tracking import MultiPersonTracker


def seconds(stamp):return stamp.sec+stamp.nanosec/1e9

class RGBDPerception(Node):
    def __init__(self,detector=None,**kwargs):
        super().__init__('rgbd_pedestrian_perception',**kwargs)
        self.registered=self.declare_parameter('registered_rectified_depth',False).value
        self.target=self.declare_parameter('target_frame','odom').value
        self.max_age=self.declare_parameter('max_observation_age',.5).value
        self.slop=self.declare_parameter('synchronization_slop',.03).value
        if not self.registered:raise ValueError('Registered rectified RGB/depth calibration must be explicitly configured')
        backend=self.declare_parameter('detector','hog').value
        manifest=self.declare_parameter('detector_manifest','').value
        if detector is not None:self.detector=detector  # dependency injection in explicitly labeled tests only
        elif backend=='hog':self.detector=HogDetector()
        elif backend=='yolo_onnx':self.detector=YoloOnnxDetector(manifest)
        else:raise ValueError('Unknown detector')
        self.backend=backend if detector is None else 'INJECTED ENGINEERING TEST FIXTURE'
        self.bridge=CvBridge();self.buffer=Buffer();self.listener=TransformListener(self.buffer,self)
        self.tracker=MultiPersonTracker();self.pending=None;self.counts=Counter();self.last_processed=-1.;self.latency=[]
        self.pub=self.create_publisher(TrackedPeople,'/tracked_people',10)
        self.status=self.create_publisher(String,'/perception/status',10)
        self.inputs=[message_filters.Subscriber(self,t,topic,qos_profile=qos_profile_sensor_data)
          for t,topic in [(Image,'/camera/image'),(Image,'/camera/depth_image'),(CameraInfo,'/camera/camera_info')]]
        self.sync=message_filters.ApproximateTimeSynchronizer(self.inputs,queue_size=10,slop=self.slop)
        self.sync.registerCallback(self.synchronized)
        self.create_timer(.02,self.process)
        self.create_timer(1.,self.report)

    def synchronized(self,rgb,depth,info):
        stamps=[seconds(m.header.stamp) for m in (rgb,depth,info)]
        if max(stamps)-min(stamps)>self.slop:self.counts['sync_rejected']+=1;return
        if len({m.header.frame_id for m in (rgb,depth,info)})!=1 or not rgb.header.frame_id:
            self.counts['frame_rejected']+=1;return
        if stamps[0]<=self.last_processed:self.counts['reordered_rejected']+=1;return
        if self.pending is not None:self.counts['overwritten_frames']+=1
        self.pending=(rgb,depth,info);self.counts['synchronized']+=1

    def process(self):
        if self.pending is None:return
        rgb,depth,info=self.pending;stamp=seconds(rgb.header.stamp)
        age=self.get_clock().now().nanoseconds/1e9-stamp
        if not 0<=age<=self.max_age:
            self.pending=None;self.counts['stale_rejected']+=1;return
        try:
            # Never use Time() / latest TF for delayed camera observations.
            transform=self.buffer.lookup_transform(self.target,rgb.header.frame_id,Time.from_msg(rgb.header.stamp))
        except TransformException:
            self.counts['tf_waits']+=1;return  # retry until observation deadline; no false empty detections
        self.pending=None;start=time.perf_counter()
        try:
            intrinsics=calibrated_intrinsics(info,rgb.width,rgb.height)
            image=self.bridge.imgmsg_to_cv2(rgb,'rgb8')
            if depth.encoding=='32FC1':z=self.bridge.imgmsg_to_cv2(depth,'passthrough').astype(np.float32)
            elif depth.encoding=='16UC1':z=self.bridge.imgmsg_to_cv2(depth,'passthrough').astype(np.float32)*.001
            else:raise ValueError('Unsupported depth encoding')
            if np.count_nonzero(np.isfinite(z) & (z>.1) & (z<20))<5:
                raise ValueError('Depth frame has no valid metric measurements')
            boxes=self.detector(image)
            tr=transform.transform.translation;q=transform.transform.rotation
            observations=metric_observations(image,z,boxes,intrinsics,(tr.x,tr.y,tr.z),(q.x,q.y,q.z,q.w))
            # Inference itself can exceed the freshness budget.
            if self.get_clock().now().nanoseconds/1e9-stamp>self.max_age:
                self.counts['inference_stale']+=1;return
            tracks=self.tracker.update(observations,stamp)
            msg=TrackedPeople();msg.header.stamp=rgb.header.stamp;msg.header.frame_id=self.target
            for track_id,t in tracks.items():
                p=TrackedPerson(track_id=track_id,hits=t.hits)
                p.observed_at.sec=int(t.stamp);p.observed_at.nanosec=round((t.stamp%1)*1e9)
                if p.observed_at.nanosec==1000000000:p.observed_at.sec+=1;p.observed_at.nanosec=0
                p.position.x=t.x;p.position.y=t.y;p.velocity.x=t.vx;p.velocity.y=t.vy
                msg.people.append(p)
            self.pub.publish(msg);self.last_processed=stamp;self.counts['published']+=1
            self.counts['boxes']+=len(boxes);self.counts['metric_observations']+=len(observations)
            self.latency.append((time.perf_counter()-start)*1000)
            self.latency=self.latency[-1000:]
        except (ValueError,TypeError,RuntimeError) as error:
            self.counts['invalid_frame']+=1;self.get_logger().warning(str(error))

    def report(self):
        result=dict(detector=self.backend,counts=dict(self.counts),latency_ms_p50=float(np.median(self.latency)) if self.latency else None)
        self.status.publish(String(data=json.dumps(result)))

def main(args=None):
    rclpy.init(args=args);node=RGBDPerception()
    try:rclpy.spin(node)
    except (KeyboardInterrupt,ExternalShutdownException):pass
    finally:node.destroy_node();rclpy.try_shutdown()
