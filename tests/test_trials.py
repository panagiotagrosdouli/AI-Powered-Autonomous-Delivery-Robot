import unittest
from research.trials import summarize
class TrialTests(unittest.TestCase):
    def rows(self):
        return [dict(condition=c,scenario='fixture',seed=1,success=False,collision=True,
          minimum_clearance_m=0,navigation_time_s=5,path_length_m=1,interventions=2) for c in 'ABCD']
    def test_failures_retained(self):
        result=summarize(self.rows())
        self.assertEqual(result['D']['success_rate'],0)
        self.assertEqual(result['D']['collision_rate'],1)
        self.assertEqual(result['D']['n'],1)
    def test_missing_condition_rejected(self):
        with self.assertRaises(ValueError):summarize(self.rows()[:-1])
    def test_missing_measurement_rejected(self):
        rows=self.rows();rows[0]['minimum_clearance_m']=None
        with self.assertRaises(ValueError):summarize(rows)
    def test_duplicate_trial_rejected(self):
        rows=self.rows()
        with self.assertRaises(ValueError):summarize(rows+[rows[0]])
