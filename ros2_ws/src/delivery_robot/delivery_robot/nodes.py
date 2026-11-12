"""ROS 2 integration. All pedestrian positions are in odom metres."""
from math import atan2, sin, cos, isfinite
from rclpy.qos import qos_profile_sensor_data
from delivery_interfaces.msg import PredictedTrack, PredictedTracks
from builtin_interfaces.msg import Duration
from geometry_msgs.msg import Point
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, PoseArray, Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from .algorithms import Tracker, scan_clearance, gate_velocity


class Predictor(Node):
    def __init__(self):
        super().__init__('pedestrian_predictor')
        self.tracker = Tracker()
        self.prediction_step = self.declare_parameter('prediction_step', 0.4).value
        self.prediction_steps = self.declare_parameter('prediction_steps', 12).value
        if not isfinite(self.prediction_step) or self.prediction_step <= 0 or self.prediction_steps < 1:
            raise ValueError('Positive prediction interval and steps required')
        self.observations_at = None
        self.neural = None
        checkpoint = self.declare_parameter('checkpoint', '').value
        allow_synthetic = self.declare_parameter('allow_synthetic_checkpoint', False).value
        if checkpoint:
            from .neural import NeuralAdapter
            self.neural = NeuralAdapter(checkpoint, allow_synthetic)
        self.create_subscription(PoseArray, '/detected_people', self.on_people, 10)
        self.pub = self.create_publisher(PredictedTracks, '/predicted_people', 10)
        self.create_timer(0.1, self.publish)

    def now(self):
        return self.get_clock().now().nanoseconds/1e9

    def on_people(self, msg):
        if msg.header.frame_id != 'odom':
            self.get_logger().warning('Expected odom-frame metric detections')
            return
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        if not 0 <= self.now() - stamp <= 0.6:
            return
        if self.observations_at is not None and stamp <= self.observations_at:
            return
        try:
            self.tracker.update([(p.position.x, p.position.y) for p in msg.poses], stamp)
        except ValueError:
            return
        self.observations_at = stamp
        if self.neural is not None:
            self.neural.update(self.tracker.tracks)

    def publish(self):
        if self.observations_at is None:
            return
        now = self.now()
        learned = self.neural.forecast(self.tracker.tracks, now) if self.neural else None
        if self.neural and learned is None:
            return
        msg = PredictedTracks()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'odom'
        msg.observations_at.sec = int(self.observations_at)
        msg.observations_at.nanosec = int((self.observations_at % 1) * 1e9)
        for track_id, t in self.tracker.tracks.items():
            age = now - t.timestamp
            if not 0 <= age <= self.tracker.max_age:
                continue
            track = PredictedTrack(track_id=track_id)
            track.observed_at.sec = int(t.timestamp)
            track.observed_at.nanosec = int((t.timestamp % 1) * 1e9)
            samples = learned.get(track_id, []) if learned is not None else [
                (k*self.prediction_step, t.x+t.vx*(age+k*self.prediction_step), t.y+t.vy*(age+k*self.prediction_step))
                for k in range(1,self.prediction_steps+1)]
            for dt, x, y in samples:
                track.offsets.append(Duration(sec=int(dt), nanosec=int(dt % 1 * 1e9)))
                track.positions.append(Point(x=x, y=y))
            msg.tracks.append(track)
        self.pub.publish(msg)


class Supervisor(Node):
    def __init__(self):
        super().__init__('safety_supervisor')
        self.condition = self.declare_parameter('condition', 'C').value
        if self.condition not in ('B','C','D'):
            raise ValueError('Supervisor condition must be B, C or D; A bypasses supervisor')
        self.command = None
        self.clearance = None
        self.pose = None
        self.forecasts = []
        self.stamps = {}
        self.create_subscription(Twist, '/cmd_vel_nav', self.on_command, 10)
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)
        self.create_subscription(Odometry, '/odom', self.on_odom, qos_profile_sensor_data)
        self.create_subscription(PredictedTracks, '/predicted_people', self.on_predictions, 10)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(0.05, self.tick)

    def now(self):
        return self.get_clock().now().nanoseconds/1e9

    def on_command(self, msg):
        values = (msg.linear.x,msg.linear.y,msg.linear.z,msg.angular.x,msg.angular.y,msg.angular.z)
        if not all(isfinite(v) for v in values) or any(v != 0 for v in (msg.linear.y,msg.linear.z,msg.angular.x,msg.angular.y)):
            self.command = None
            return
        self.command = msg
        self.stamps['command'] = self.now()

    def on_scan(self, msg):
        if msg.header.frame_id != 'laser':
            self.clearance = None
            return
        self.clearance = scan_clearance(msg.ranges, msg.angle_min,
                                        msg.angle_increment, msg.range_min, msg.range_max)
        self.stamps['scan'] = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9

    def on_odom(self, msg):
        if msg.header.frame_id != 'odom' or msg.child_frame_id != 'base_link':
            self.pose = None
            return
        q = msg.pose.pose.orientation
        if not all(isfinite(z) for z in (q.x,q.y,q.z,q.w)) or abs(q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w-1) > 1e-3:
            self.pose = None
            return
        yaw = atan2(2*(q.w*q.z + q.x*q.y), 1-2*(q.y*q.y + q.z*q.z))
        p = msg.pose.pose.position
        self.pose = p.x, p.y, yaw
        self.stamps['odom'] = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9

    def on_predictions(self, msg):
        if msg.header.frame_id != 'odom':
            return
        origin = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        observed = msg.observations_at.sec + msg.observations_at.nanosec / 1e9
        now = self.now()
        if not 0 <= now - origin <= 0.6 or not 0 <= now - observed <= 0.6:
            return
        forecasts = []
        ids = set()
        for track in msg.tracks:
            if track.track_id in ids or not track.positions:
                return
            ids.add(track.track_id)
            stamp = track.observed_at.sec + track.observed_at.nanosec / 1e9
            if not 0 <= now - stamp <= 0.6 or len(track.offsets) != len(track.positions):
                return
            last = 0.0
            for offset, p in zip(track.offsets, track.positions):
                dt = offset.sec + offset.nanosec / 1e9
                if dt <= last or not all(isfinite(z) for z in (dt, p.x, p.y)):
                    return
                last = dt
                remaining = dt - (now - origin)
                if remaining >= 0:
                    forecasts.append((remaining, p.x, p.y))
        self.forecasts = forecasts
        self.stamps['predictions'] = min(origin, observed)

    def tick(self):
        output = Twist()  # fail closed by default
        now = self.now()
        limits = {'command': 0.5, 'scan': 0.6, 'odom': 0.6, 'predictions': 0.6}
        if self.condition == 'B':
            del limits['predictions']
        fresh = all(k in self.stamps and 0 <= now-self.stamps[k] <= max_age
                    for k, max_age in limits.items())
        if fresh and self.command is not None and self.pose is not None:
            v, w = gate_velocity(self.command.linear.x, self.command.angular.z,
                                 self.clearance, self.pose, self.forecasts if self.condition != 'B' else [])
            output.linear.x, output.angular.z = v, w
        self.pub.publish(output)


class SyntheticPeople(Node):
    def __init__(self):
        super().__init__('synthetic_people')
        self.pub = self.create_publisher(PoseArray, '/detected_people', 10)
        self.start = self.get_clock().now().nanoseconds / 1e9
        self.create_timer(0.1, self.tick)

    def tick(self):
        now = self.get_clock().now()
        t = now.nanoseconds/1e9-self.start
        msg = PoseArray()
        msg.header.frame_id = 'odom'
        msg.header.stamp = now.to_msg()
        for x, y in [(2., 1. - (t*0.25)%2), (3.5, sin(t*0.6))]:
            pose = Pose()
            pose.position.x, pose.position.y, pose.orientation.w = x, y, 1.
            msg.poses.append(pose)
        self.pub.publish(msg)


def run(cls, args=None):
    rclpy.init(args=args)
    node = cls()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


def predictor_main(args=None):
    run(Predictor, args)


def supervisor_main(args=None):
    run(Supervisor, args)


def demo_main(args=None):
    run(SyntheticPeople, args)
