#!/usr/bin/env python3
"""Fetch authors' published ETH/UCY archive; NOT a license grant or training approval."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

URL='https://www.dropbox.com/s/8n02xqv3l9q18r1/datasets.zip?dl=1'
SCRIPT='https://github.com/agrimgupta92/sgan/blob/691231e1adb6a344c7bcea9ebf2534518b226ead/scripts/download_data.sh'

def inspect(archive):
    import numpy as np
    files=[]
    with zipfile.ZipFile(archive) as z:
        for name in z.namelist():
            if not name.endswith('.txt'):continue
            raw=z.read(name);data=np.loadtxt(raw.splitlines(),ndmin=2)
            if data.shape[1]!=4 or not np.isfinite(data).all():raise ValueError('Invalid trajectory format: '+name)
            if len(np.unique(data[:,:2],axis=0))!=len(data):raise ValueError('Duplicate frame/ID pair: '+name)
            files.append(dict(path=name,sha256=hashlib.sha256(raw).hexdigest(),rows=len(data),
              tracks=len(np.unique(data[:,1])),frame_min=float(data[:,0].min()),frame_max=float(data[:,0].max())))
    return dict(source=URL,source_script=SCRIPT,archive_sha256=hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
      real_recorded_trajectory_archive=True,license_verified=False,
      license_note='No dataset license found in archive. Code MIT license does not establish dataset rights.',
      coordinate_units='Upstream processed coordinates; metric units require original dataset verification',
      sampling='Frame indices preserved; seconds conversion requires source metadata verification',
      training_status='BLOCKED pending verified dataset terms, coordinate and sampling metadata',files=files)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--existing-archive',type=Path);p.add_argument('--record',type=Path,required=True);a=p.parse_args()
    a.directory.mkdir(parents=True,exist_ok=True)
    archive=a.existing_archive or a.directory/'datasets.zip'
    if a.existing_archive is None:
        with urllib.request.urlopen(URL,timeout=60) as source,archive.open('wb') as target:
            while chunk:=source.read(1024*1024):target.write(chunk)
    a.record.write_text(json.dumps(inspect(archive),indent=2))
