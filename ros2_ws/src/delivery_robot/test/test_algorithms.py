import unittest
from delivery_robot.algorithms import Tracker, gate_velocity, scan_clearance, will_conflict


class AlgorithmTests(unittest.TestCase):
    def test_forecast(self):
        t = Tracker()
        t.update([(0., 0.)], 1.)
        t.update([(0.5, 0.)], 1.5)
        self.assertGreater(t.forecast(1.5)[0][1], 0.5)

    def test_expiration(self):
        t = Tracker(max_age=0.5)
        t.update([(0., 0.)], 1.)
        self.assertEqual(t.forecast(2.), [])

    def test_scan_missing(self):
        self.assertIsNone(scan_clearance([float('inf')], 0, 1, 0.1, 10))

    def test_scan_close(self):
        self.assertEqual(gate_velocity(0.5, 0., 0.4, (0, 0, 0), []), (0., 0.))

    def test_collision(self):
        self.assertTrue(will_conflict(0, 0, 0, 1, 0, [(1, 1, 0.1)]))

    def test_speed_reduction(self):
        self.assertAlmostEqual(gate_velocity(0.4, 0., 0.95, (0, 0, 0), [])[0], 0.2)


if __name__ == '__main__':
    unittest.main()
