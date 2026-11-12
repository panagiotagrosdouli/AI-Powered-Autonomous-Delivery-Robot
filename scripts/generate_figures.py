#!/usr/bin/env python3
"""Figures only from saved executed evidence. No fallback or expected values."""
import json
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/delivery-matplotlib')
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'evidence/figures';out.mkdir(exist_ok=True)
m=json.loads((root/'evidence/mapping/occupancy.json').read_text())
path=json.loads((root/'evidence/navigation/odom_path.json').read_text())
fig,axes=plt.subplots(1,2,figsize=(9,4),layout='constrained')
a=np.array(m['data']).reshape(m['height'],m['width']);res=m['resolution'];x,y,_=m['origin']
axes[0].imshow(a,origin='lower',cmap='gray_r',vmin=-1,vmax=100,
  extent=[x,x+m['width']*res,y,y+m['height']*res])
axes[0].set(title='Measured simulated-LiDAR SLAM map',xlabel='Map x (m)',ylabel='Map y (m)')
axes[1].plot([p['x'] for p in path],[p['y'] for p in path])
axes[1].set(title='Measured Nav2 odometry path',xlabel='Odom x (m)',ylabel='Odom y (m)');axes[1].axis('equal');axes[1].grid(alpha=.3)
fig.savefig(out/'map_and_path.svg');plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(10,3),layout='constrained')
for ax,kind in zip(axes,['gru','lstm','transformer']):
 r=json.loads((root/f'evidence/final_synthetic_{kind}/results.json').read_text());h=r['history']
 ax.plot([v['epoch']+1 for v in h],[v['train_mse_m2'] for v in h],label='Train')
 ax.plot([v['epoch']+1 for v in h],[v['val_mse_m2'] for v in h],label='Validation')
 ax.set(title=kind.upper(),xlabel='Epoch',ylabel='MSE (m²)');ax.legend();ax.grid(alpha=.3)
fig.suptitle('SYNTHETIC software fixture — not a real pedestrian benchmark')
fig.savefig(out/'synthetic_training.svg');plt.close(fig)
