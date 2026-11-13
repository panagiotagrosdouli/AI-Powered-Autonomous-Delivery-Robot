#!/usr/bin/env python3
"""Export existing genuinely trained SYNTHETIC checkpoints, never real-data claims."""
import hashlib,json
from pathlib import Path
import numpy as np
import torch
import onnxruntime as ort
from research.models import Forecaster

def main():
 root=Path('evidence');out=Path('work/onnx-engineering');out.mkdir(parents=True,exist_ok=True)
 torch.set_num_threads(1);torch.backends.mha.set_fastpath_enabled(False)
 for kind in ('gru','lstm','transformer'):
  checkpoint_path=root/f'final_synthetic_{kind}/best.pt'
  measured=json.loads((checkpoint_path.parent/'results.json').read_text())
  digest=hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
  if digest!=measured['checkpoint_sha256']:raise ValueError('Saved trained checkpoint checksum mismatch')
  checkpoint=torch.load(checkpoint_path,weights_only=True,map_location='cpu')
  if checkpoint['data_kind']!='SYNTHETIC SOFTWARE TEST ONLY':raise ValueError('This exporter is engineering-only')
  model=Forecaster(kind,checkpoint['pred']);model.load_state_dict(checkpoint['state_dict']);model.eval()
  sample=torch.randn(1,checkpoint['obs'],2,generator=torch.Generator().manual_seed(123))
  target=out/f'{kind}.onnx'
  torch.onnx.export(model,sample,str(target),opset_version=17,input_names=['observations'],output_names=['positions'])
  session=ort.InferenceSession(str(target),providers=['CPUExecutionProvider'])
  errors=[]
  for seed in range(5):
   test=torch.randn(1,checkpoint['obs'],2,generator=torch.Generator().manual_seed(seed))
   with torch.no_grad():reference=model(test).numpy()
   actual=session.run(None,{'observations':test.numpy()})[0]
   errors.append(float(np.max(np.abs(actual-reference))))
  if max(errors)>1e-4:raise ValueError('ONNX equivalence failed')
  meta={k:checkpoint[k] for k in ('kind','obs','pred','data_kind','sample_interval_seconds')}
  meta.update(path=target.name,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
    trained_checkpoint_sha256=digest,export_max_abs_error_m=max(errors),engineering_only=True,
    export_torch=torch.__version__,export_onnxruntime=ort.__version__)
  (out/f'{kind}.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta))
if __name__=='__main__':main()
