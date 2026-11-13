import math
import unittest
from delivery_robot.algorithms import scan_clearance,gate_velocity
class FullScanTests(unittest.TestCase):
    def test_rear_obstacle_is_not_discarded(self):
        self.assertEqual(scan_clearance([.3],math.pi,.1,.1,10),.3)
    def test_speed_limits_fail_closed(self):
        for v,w in ((.51,0),(0,1.01),(-.51,0)):
            self.assertEqual(gate_velocity(v,w,2,(0,0,0),[]),(0,0))
