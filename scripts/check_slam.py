#!/usr/bin/env python3
"""Inspect live ROS 2 SLAM outputs; exits nonzero on missing data."""
import math
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
from nav_msgs.msg import OccupancyGrid, Odometry
from sensor_msgs.msg import LaserScan
from tf2_msgs.msg import TFMessage


class SlamProbe(Node):
    def __init__(self):
        super().__init__('slam_probe')
        self.seen = {'scan': False, 'odom': False, 'map': False, 'map_to_odom': False}
        self.map_cells = 0
        self.create_subscription(LaserScan, '/scan', self.scan, qos_profile_sensor_data)
        self.create_subscription(Odometry, '/odom', self.odom, qos_profile_sensor_data)
        self.create_subscription(OccupancyGrid, '/map', self.map, QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
        self.create_subscription(TFMessage, '/tf', self.tf, 30)

    def scan(self, msg):
        self.seen['scan'] = any(math.isfinite(x) and msg.range_min <= x <= msg.range_max
                                for x in msg.ranges)

    def odom(self, msg):
        self.seen['odom'] = bool(msg.header.frame_id and msg.child_frame_id)

    def map(self, msg):
        known = sum(value >= 0 for value in msg.data)
        self.seen['map'] = msg.info.width > 0 and msg.info.height > 0 and known > 0
        self.map_cells = known

    def tf(self, msg):
        for t in msg.transforms:
            if t.header.frame_id.lstrip('/') == 'map' and t.child_frame_id.lstrip('/') == 'odom':
                self.seen['map_to_odom'] = True


def main():
    rclpy.init()
    node = SlamProbe()
    deadline = time.monotonic() + 30
    try:
        while time.monotonic() < deadline and not all(node.seen.values()):
            rclpy.spin_once(node, timeout_sec=0.2)
        for name, ok in node.seen.items():
            print(f'{name}: {"PASS" if ok else "FAIL"}')
        print(f'Known occupancy cells: {node.map_cells}')
        return 0 if all(node.seen.values()) else 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
