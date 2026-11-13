import tempfile
import unittest
from pathlib import Path
import torch
from research.models import Forecaster
from delivery_robot.neural import NeuralAdapter
from delivery_robot.algorithms import Track

class NeuralAdapterTests(unittest.TestCase):
    def test_synthetic_checkpoint_refused_and_history_required(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'fixture.pt'
            torch.save(dict(kind='gru',obs=3,pred=2,sample_interval_seconds=.4,
                data_kind='SYNTHETIC SOFTWARE TEST ONLY',state_dict=Forecaster('gru',2).state_dict()),path)
            with self.assertRaises(ValueError):NeuralAdapter(path)
            adapter=NeuralAdapter(path,allow_synthetic=True)
            tracks={7:Track(0,0,1,0,0)};adapter.update(tracks)
            self.assertIsNone(adapter.forecast(tracks,0))
            for stamp in (.4,.8):
                tracks[7]=Track(stamp,0,1,0,stamp);adapter.update(tracks)
            forecasts=adapter.forecast(tracks,.8)
            self.assertEqual(len(forecasts[7]),2)
            self.assertAlmostEqual(forecasts[7][0][0],.4)
            # A missing observation interval invalidates the usable history.
            tracks[7]=Track(2,0,1,0,2);adapter.update(tracks)
            self.assertIsNone(adapter.forecast(tracks,2))
