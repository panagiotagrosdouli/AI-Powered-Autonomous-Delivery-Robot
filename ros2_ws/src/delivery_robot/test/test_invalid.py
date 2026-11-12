import math
import unittest
from delivery_robot.algorithms import Tracker, gate_velocity

class InvalidInputTests(unittest.TestCase):
    def test_nan_and_infinity_stop(self):
        for v in (math.nan, math.inf, -math.inf):
            self.assertEqual(gate_velocity(v, 0, 2, (0,0,0), []), (0,0))
            self.assertEqual(gate_velocity(.2, 0, 2, (v,0,0), []), (0,0))
            self.assertEqual(gate_velocity(.2, 0, 2, (0,0,0), [(1,v,0)]), (0,0))
    def test_full_scan_supports_reverse_and_rotation_with_limits(self):
        self.assertEqual(gate_velocity(-.2, 0, 2, (0,0,0), []), (-.2,0))
        self.assertEqual(gate_velocity(.2, .1, 2, (0,0,0), []), (.2,.1))
    def test_reordered_observation_rejected(self):
        t=Tracker(); t.update([(0,0)], 2)
        for stamp in (2,1):
            with self.assertRaises(ValueError): t.update([(1,0)], stamp)
    def test_invalid_detection_rejected(self):
        with self.assertRaises(ValueError): Tracker().update([(math.nan,0)], 1)
