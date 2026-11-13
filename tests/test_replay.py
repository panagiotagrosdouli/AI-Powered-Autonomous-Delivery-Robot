import math
import tempfile
import unittest
from pathlib import Path
import numpy as np
from research.replay import convert,pose_at
class ReplayTests(unittest.TestCase):
    def test_original_intervals_and_rigid_transform(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'fixture.txt';np.savetxt(file,[[10,1,1,0],[20,1,2,0],[40,1,4,0]])
            track=convert(file,.04,(2,3),math.pi/2)[0]
            self.assertEqual([s['t'] for s in track['samples']],[0,.4,1.2])
            self.assertAlmostEqual(track['samples'][0]['x'],2)
            self.assertAlmostEqual(track['samples'][0]['y'],4)
            self.assertAlmostEqual(pose_at(track['samples'],.2)[1],4.5)
            self.assertIsNone(pose_at(track['samples'],-.1))
    def test_duplicates_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'fixture.txt';np.savetxt(file,[[1,1,0,0],[1,1,1,1]])
            with self.assertRaises(ValueError):convert(file,.1,(0,0),0)
