import json
import tempfile
import unittest
import torch
from research.models import Forecaster,constant_velocity,displacement_errors
from research.data import load_manifest
from research.synthetic_fixture import make

class ResearchTests(unittest.TestCase):
    def test_models_backward_and_translation(self):
        torch.set_num_threads(1)
        for kind in ('gru','lstm','transformer'):
            m=Forecaster(kind);x=torch.randn(3,8,2)
            y=m(x);self.assertEqual(tuple(y.shape),(3,12,2))
            self.assertTrue(torch.allclose(m(x+10),y+10,atol=2e-5))
            y.square().mean().backward()
            self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in m.parameters()))
    def test_cv_exact_and_metric(self):
        x=torch.tensor([[[0.,0.],[1.,0.]]]);target=torch.tensor([[[2.,0.],[3.,0.]]])
        ade,fde=displacement_errors(constant_velocity(x,2),target)
        self.assertEqual(ade.item(),0);self.assertEqual(fde.item(),0)
        ade,fde=displacement_errors(target+torch.tensor([3.,4.]),target)
        self.assertEqual(ade.item(),5);self.assertEqual(fde.item(),5)
    def test_split_leakage_and_checksum_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=make(d);splits,_=load_manifest(path);self.assertGreater(len(splits['test']),0)
            meta=json.loads(path.read_text());meta['test']=meta['train'];path.write_text(json.dumps(meta))
            with self.assertRaises(ValueError):load_manifest(path)
    def test_unverified_license_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=make(d);meta=json.loads(path.read_text());meta['license_verified']=False
            path.write_text(json.dumps(meta))
            with self.assertRaises(ValueError):load_manifest(path)
