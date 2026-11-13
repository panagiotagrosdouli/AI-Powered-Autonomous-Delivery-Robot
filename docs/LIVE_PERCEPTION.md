# Live RGB-D perception continuation

The live node synchronizes RGB, registered depth and CameraInfo with a bounded
30 ms slop; validates rectified pinhole calibration, resolution, distortion and
ROI; rejects invalid depth; runs actual OpenCV HOG or a verified local YOLOv8
ONNX export; extracts robust torso depth; and transforms points using TF at the
RGB observation timestamp. Missing TF is retried only within the observation
freshness budget. Failures never publish a false healthy empty observation.
The explicit registered_rectified_depth flag is a required sensor assertion,
not automatic proof that a physical camera has been calibrated or registered.

Tracking uses velocity-predicted Hungarian assignment, appearance histograms and
bounded occlusion retention. IDs, observation times, metric positions and velocity
are published in TrackedPeople. The predictor's input_mode=tracked consumes these
IDs directly instead of performing a second association. Identity is not guaranteed
under indistinguishable appearance, long occlusion or abrupt motion.

```
ros2 launch delivery_robot perception.launch.py registered_rectified_depth:=true
```

Only assert registration for a correctly configured registered RGB-D source. The
custom Gazebo RGB-D sensor is co-registered and supplies zero-distortion CameraInfo.
Its captured K and frame IDs are recorded in phase2/live-perception-probe.json.
HOG is OpenCV's distributed people SVM, not YOLO and not a newly trained model.
YOLO mode requires detector:=yolo_onnx plus detector_manifest containing local
path, sha256, input_size and license_verified=true. That declaration requires
independent rights verification; this project has not provisioned YOLO weights.

Executed evidence:

- test_live_perception.py passed with explicitly injected synthetic boxes. A
  delayed camera observation produced odom x=3 using its historical TF, rather
  than x=11 from latest TF. Unknown TF expired without a healthy publication;
  nonzero distortion and stale timestamps were rejected.
- Actual Gazebo camera frames passed synchronization, HOG inference, calibration,
  observation-time TF and tracker/predictor transport. The captured run recorded
  156 published observations and median processing latency 23.5979855 ms.
- That scene contains no human models. There were zero detections; this run is
  NOT pedestrian detection accuracy, tracking accuracy or navigation evidence.
- Unit tests exercise crossing identity, bounded occlusion, expiration, optimal
  assignment, depth holes and calibration mismatch.

The first live run exposed an already-shutdown exception at harness SIGINT. The
node shutdown paths were corrected to catch shutdown and use try_shutdown; the
original log remains preserved. Positive live pedestrian detection with verified
weights/data and full predictive navigation are still outstanding.
