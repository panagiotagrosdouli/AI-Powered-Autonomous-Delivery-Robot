import math
import unittest
from delivery_robot.perception import deproject,transform_point
class GeometryTests(unittest.TestCase):
    def test_metric_optical_projection(self):
        self.assertEqual(deproject(420,240,2,500,500,320,240),(.4,0,2))
    def test_optical_to_robot_rotation(self):
        # optical z forward -> robot x forward; optical x right -> robot -y
        self.assertEqual(transform_point((0,0,2),(1,0,0),(-.5,.5,-.5,.5)),(3,0,0))
    def test_reject_missing_depth(self):
        for d in (0,-1,math.nan,math.inf):
            with self.assertRaises(ValueError):deproject(0,0,d,1,1,0,0)
    def test_reject_bad_quaternion(self):
        with self.assertRaises(ValueError):transform_point((0,0,0),(0,0,0),(0,0,0,0))
