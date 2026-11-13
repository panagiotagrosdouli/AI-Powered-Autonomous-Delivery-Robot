import unittest
from types import SimpleNamespace
import numpy as np
from delivery_robot.rgbd import calibrated_intrinsics,metric_observations
class RGBDTests(unittest.TestCase):
    def info(self):
        return SimpleNamespace(width=200,height=160,binning_x=0,binning_y=0,
          roi=SimpleNamespace(x_offset=0,y_offset=0,width=0,height=0),d=[0]*5,
          k=[100,0,100,0,100,80,0,0,1])
    def test_metric_depth_and_extrinsics(self):
        intrinsics=calibrated_intrinsics(self.info(),200,160)
        image=np.zeros((160,200,3),dtype=np.uint8);depth=np.full((160,200),2.)
        obs=metric_observations(image,depth,[(80,20,120,140,.9)],intrinsics,(1,0,0),(-.5,.5,-.5,.5))
        self.assertAlmostEqual(obs[0][0],3);self.assertAlmostEqual(obs[0][1],0)
    def test_depth_holes_never_invent_distance(self):
        image=np.zeros((160,200,3),dtype=np.uint8);depth=np.full((160,200),np.nan)
        self.assertEqual(metric_observations(image,depth,[(80,20,120,140,.9)],
          calibrated_intrinsics(self.info(),200,160),(0,0,0),(0,0,0,1)),[])
    def test_calibration_mismatch_rejected(self):
        i=self.info();i.d=[.1]
        with self.assertRaises(ValueError):calibrated_intrinsics(i,200,160)
        with self.assertRaises(ValueError):calibrated_intrinsics(self.info(),100,80)
