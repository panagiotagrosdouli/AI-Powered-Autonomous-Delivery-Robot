"""Actual training and held-out evaluation; never invent benchmark records."""
import argparse
import hashlib
import json
import platform
import time
from pathlib import Path
import numpy as np
import torch
from .data import load_manifest
from .models import Forecaster, constant_velocity, displacement_errors

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--kind',choices=['gru','lstm','transformer'],required=True)
    p.add_argument('--obs',type=int,default=8);p.add_argument('--pred',type=int,default=12)
    p.add_argument('--epochs',type=int,default=20);p.add_argument('--batch',type=int,default=64)
    p.add_argument('--seed',type=int,default=42)
    a=p.parse_args()
    if a.epochs < 1 or a.obs < 2 or a.pred < 1 or a.batch < 1: p.error('Invalid horizons/training settings')
    a.output.mkdir(parents=True,exist_ok=False)
    torch.manual_seed(a.seed);np.random.seed(a.seed);torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    splits,meta=load_manifest(a.manifest,a.obs,a.pred)
    tensors={k:torch.from_numpy(v) for k,v in splits.items()}
    model=Forecaster(a.kind,a.pred)
    opt=torch.optim.Adam(model.parameters(),lr=1e-3)
    best=float('inf');history=[]
    start=time.perf_counter()
    for epoch in range(a.epochs):
        model.train(); total=0
        for idx in torch.randperm(len(tensors['train'])).split(a.batch):
            seq=tensors['train'][idx];opt.zero_grad()
            loss=(model(seq[:,:a.obs])-seq[:,a.obs:]).square().mean()
            loss.backward(); opt.step();total+=loss.item()*len(idx)
        model.eval()
        with torch.no_grad():
            v=tensors['val'];val=(model(v[:,:a.obs])-v[:,a.obs:]).square().mean().item()
        history.append(dict(epoch=epoch,train_mse_m2=total/len(tensors['train']),val_mse_m2=val))
        if val < best:
            best=val;torch.save(dict(state_dict=model.state_dict(),kind=a.kind,obs=a.obs,pred=a.pred,data_kind=meta['data_kind'],sample_interval_seconds=meta['sample_interval_seconds']),a.output/'best.pt')
    training_seconds=time.perf_counter()-start
    model.load_state_dict(torch.load(a.output/'best.pt',weights_only=True)['state_dict']);model.eval()
    test=tensors['test'];results={}
    with torch.no_grad():
        for name,fn in [(a.kind,model),('cv',lambda x:constant_velocity(x,a.pred))]:
            # Warm-up, then batch-one wall-time latency on this CPU executor.
            for _ in range(5): fn(test[:1,:a.obs])
            latency=[];predictions=[]
            for seq in test:
                t=time.perf_counter();predictions.append(fn(seq[None,:a.obs]));latency.append((time.perf_counter()-t)*1000)
            ade,fde=displacement_errors(torch.cat(predictions),test[:,a.obs:])
            np.savez(a.output/f'{name}_per_window.npz',ade_m=ade.numpy(),fde_m=fde.numpy(),latency_ms=latency)
            results[name]=dict(ade_m=ade.mean().item(),fde_m=fde.mean().item(),latency_ms_p50=float(np.median(latency)),latency_ms_p95=float(np.percentile(latency,95)))
    record=dict(data_kind=meta['data_kind'],source=meta['source'],dataset_manifest=meta,
      manifest_sha256=hashlib.sha256(a.manifest.read_bytes()).hexdigest(),
      split_windows={k:len(v) for k,v in tensors.items()},results=results,history=history,
      training_seconds=training_seconds,torch=torch.__version__,python=platform.python_version(),
      cpu=platform.processor(),threads=1,seed=a.seed,epochs=a.epochs,obs=a.obs,pred=a.pred,
      checkpoint_sha256=hashlib.sha256((a.output/'best.pt').read_bytes()).hexdigest())
    (a.output/'results.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(results,indent=2))

if __name__=='__main__':main()
