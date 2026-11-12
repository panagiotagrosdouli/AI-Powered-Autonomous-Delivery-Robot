import csv
import tempfile
import unittest
from pathlib import Path

from trajectory_forecasting.data import load_windows, read_tracks
from trajectory_forecasting.metrics import (constant_velocity, displacement_errors,
                                            evaluate_constant_velocity)
from trajectory_forecasting.train import _scene_sets


class TrajectoryPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "tracks.csv"
        with self.path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["scene_id", "pedestrian_id", "frame", "x", "y"])
            for frame in range(25):
                writer.writerow(["scene-A", "p1", frame, frame * 0.5, 1.0])
                writer.writerow(["scene-B", "p2", frame, 100 + frame, 0])

    def tearDown(self):
        self.temp.cleanup()

    def test_scene_filter_and_window_horizons(self):
        windows = load_windows(self.path, {"scene-A"}, 8, 12, 5)
        self.assertEqual(len(windows), 2)
        self.assertTrue(all(w.scene_id == "scene-A" for w in windows))
        self.assertEqual((len(windows[0].observation), len(windows[0].future)), (8, 12))

    def test_missing_frames_are_not_bridged(self):
        rows = self.path.read_text(encoding="utf-8").replace("scene-A,p1,10,5.0,1.0\n", "")
        self.path.write_text(rows, encoding="utf-8")
        windows = load_windows(self.path, {"scene-A"}, 8, 12)
        self.assertTrue(all(len(w.observation) == 8 for w in windows))
        self.assertTrue(all(w.future[-1][0] - w.future[0][0] == 11 * 0.5 for w in windows))

    def test_duplicate_frames_rejected(self):
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write("scene-A,p1,0,0,1\n")
        with self.assertRaisesRegex(ValueError, "Duplicate frame"):
            read_tracks(self.path)

    def test_constant_velocity_metrics(self):
        pred = constant_velocity(((0, 0), (1, 0)), 2)
        self.assertEqual(pred, ((2, 0), (3, 0)))
        self.assertEqual(displacement_errors(pred, ((2, 1), (3, 2))), (1.5, 2.0))
        result = evaluate_constant_velocity(load_windows(self.path, {"scene-A"}, 8, 12, 20))
        self.assertEqual(result["windows"], 1)
        self.assertGreaterEqual(result["ADE_m"], 0)

    def test_scene_split_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be disjoint"):
            _scene_sets(["scene-A"], ["scene-A"])


if __name__ == "__main__":
    unittest.main()
