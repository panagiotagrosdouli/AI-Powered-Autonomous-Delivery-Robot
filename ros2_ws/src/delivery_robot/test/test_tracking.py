import unittest
from delivery_robot.tracking import MultiPersonTracker,assignment

class TrackingTests(unittest.TestCase):
    def test_global_not_greedy(self):
        self.assertEqual(sorted(assignment([[1,2],[1.1,100]])),[(0,1),(1,0)])
    def test_crossing_identity_and_occlusion(self):
        tracker=MultiPersonTracker(gate=2,max_age=.8)
        tracks=tracker.update([(-1,0,(1,0)),(1,0,(0,1))],0)
        for stamp,x in ((.2,-.5),(.4,0),(.6,.5)):
            tracks=tracker.update([(x,0,(1,0)),(-x,0,(0,1))],stamp)
        self.assertGreater(tracks[1].x,tracks[2].x)
        tracker.update([], .8)
        tracks=tracker.update([(1.5,0,(1,0)),(-1.5,0,(0,1))],1.)
        self.assertEqual(set(tracks),{1,2})
        self.assertGreater(tracks[1].x,0)
    def test_expiration_does_not_reuse_id(self):
        t=MultiPersonTracker();t.update([(0,0,())],0);t.update([],1)
        self.assertEqual(set(t.update([(0,0,())],1.1)),{2})
    def test_reordered_frame_rejected(self):
        t=MultiPersonTracker();t.update([],2)
        with self.assertRaises(ValueError):t.update([],1)
