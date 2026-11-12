"""Generate explicitly SYNTHETIC model plumbing fixtures, never research evidence."""
import hashlib
import json
from pathlib import Path
import numpy as np

def make(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    meta=dict(units='metres',license_verified=True,license='Project-generated synthetic data; MIT',
      sample_interval_seconds=.4,frame_stride=1,data_kind='SYNTHETIC SOFTWARE TEST ONLY',
      source='research.synthetic_fixture; generated analytical motion, not recorded pedestrians')
    rng=np.random.default_rng(17)
    for split in ('train','val','test'):
        rows=[]
        for pid in range(6):
            velocity=rng.uniform(-.4,.4,2);origin=rng.uniform(-3,3,2)
            acceleration=rng.uniform(-.002,.002,2)
            for frame in range(30):
                xy=origin+frame*velocity+frame**2*acceleration
                rows.append([frame,pid,*xy])
        file=directory/f'{split}.txt';np.savetxt(file,rows)
        meta[split]=[dict(path=file.name,scene_id=split,sha256=hashlib.sha256(file.read_bytes()).hexdigest())]
    path=directory/'manifest.json';path.write_text(json.dumps(meta,indent=2));return path

if __name__=='__main__':
    import sys
    print(make(sys.argv[1]))
