"""ROS 2 integration. All pedestrian positions are in odom metres."""
from math import atan2, sin, cos
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
        self.create_subscription(PoseArray, '/detected_people', self.on_people, 10)
        self.pub = self.create_publisher(PoseArray, '/predicted_people', 10)
        self.create_timer(0.1, self.publish)

    def now(self):
        return self.get_clock().now().nanoseconds/1e9

    def on_people(self, msg):
        if msg.header.frame_id != 'odom':
            self.get_logger().warning('Expected odom-frame metric detections')
            return
        self.tracker.update([(p.position.x, p.position.y) for p in msg.poses],
                            self.now())

    def publish(self):
        msg = PoseArray()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'odom'
        for _, x, y in self.tracker.forecast(self.now()):
            pose = Pose()
            pose.position.x, pose.position.y, pose.orientation.w = x, y, 1.
            msg.poses.append(pose)
        self.pub.publish(msg)


class Supervisor(Node):
    def __init__(self):
        super().__init__('safety_supervisor')
        self.command = None
        self.clearance = None
        self.pose = None
        self.forecasts = []
        self.stamps = {}
        self.create_subscription(Twist, '/cmd_vel_nav', self.on_command, 10)
        self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, 10)
        self.create_subscription(PoseArray, '/predicted_people', self.on_predictions, 10)
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(0.05, self.tick)

    def now(self):
        return self.get_clock().now().nanoseconds/1e9

    def on_command(self, msg):
        self.command = msg
        self.stamps['command'] = self.now()

    def on_scan(self, msg):
        self.clearance = scan_clearance(msg.ranges, msg.angle_min,
                                        msg.angle_increment, msg.range_min, msg.range_max)
        self.stamps['scan'] = self.now()

    def on_odom(self, msg):
        if msg.header.frame_id != 'odom':
            return
        q = msg.pose.pose.orientation
        yaw = atan2(2*(q.w*q.z + q.x*q.y), 1-2*(q.y*q.y + q.z*q.z))
        p = msg.pose.pose.position
        self.pose = p.x, p.y, yaw
        self.stamps['odom'] = self.now()

    def on_predictions(self, msg):
        if msg.header.frame_id != 'odom':
            return
        # Flattened fixed 0.25 s samples: prototype, loses track identities.
        self.forecasts = [((k % 8 + 1)*0.25, p.position.x, p.position.y)
                          for k, p in enumerate(msg.poses)]
        self.stamps['predictions'] = self.now()

    def tick(self):
        output = Twist()  # fail closed by default
        now = self.now()
        limits = {'command': 0.5, 'scan': 0.6, 'odom': 0.6, 'predictions': 0.6}
        fresh = all(k in self.stamps and 0 <= now-self.stamps[k] <= max_age
                    for k, max_age in limits.items())
        if fresh and self.command is not None and self.pose is not None:
            v, w = gate_velocity(self.command.linear.x, self.command.angular.z,
                                 self.clearance, self.pose, self.forecasts)
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
