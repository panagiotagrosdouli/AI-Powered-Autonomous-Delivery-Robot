"""Four-column frame,id,x_m,y_m trajectory data; scene-level split only."""
import hashlib
import json
from pathlib import Path
import numpy as np

def load_manifest(path, obs=8, pred=12):
    path = Path(path)
    manifest = json.loads(path.read_text())
    if manifest.get('units') != 'metres' or manifest.get('license_verified') is not True:
        raise ValueError('Metric units and verified dataset permission are required')
    dt = float(manifest['sample_interval_seconds'])
    stride = float(manifest['frame_stride'])
    if dt <= 0 or stride <= 0 or not np.isfinite([dt, stride]).all():
        raise ValueError('Invalid sampling metadata')
    splits = {}; seen = set(); scene_splits = {}
    for split in ('train','val','test'):
        windows = []
        for item in manifest[split]:
            scene = item['scene_id']
            if scene in scene_splits and scene_splits[scene] != split:
                raise ValueError('Recording scene appears in multiple splits')
            scene_splits[scene] = split
            file = path.parent / item['path']
            digest = hashlib.sha256(file.read_bytes()).hexdigest()
            if digest != item['sha256'] or digest in seen:
                raise ValueError('Checksum mismatch or duplicated scene across splits')
            seen.add(digest)
            data = np.loadtxt(file, ndmin=2)
            if data.shape[1] != 4 or not np.isfinite(data).all():
                raise ValueError('Expected finite frame,id,x_m,y_m rows')
            if len(np.unique(data[:,:2], axis=0)) != len(data):
                raise ValueError('Duplicate frame/track pair')
            for pid in np.unique(data[:,1]):
                rows = data[data[:,1] == pid]; rows = rows[np.argsort(rows[:,0])]
                for start in range(len(rows)-obs-pred+1):
                    seq = rows[start:start+obs+pred]
                    if np.allclose(np.diff(seq[:,0]), stride):
                        windows.append(seq[:,2:4])
        if not windows:
            raise ValueError(f'No contiguous windows in {split}')
        splits[split] = np.asarray(windows, dtype=np.float32)
    return splits, manifest
