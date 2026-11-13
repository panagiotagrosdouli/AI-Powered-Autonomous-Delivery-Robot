"""Summarize measured matched trials. Missing/failed trials are never filtered."""
import argparse
import json
import math
from pathlib import Path
import numpy as np

def summarize(records):
    if not records: raise ValueError('No actual trials supplied')
    conditions=('A','B','C','D');keys={}; groups={c:[] for c in conditions}
    for row in records:
        c=row['condition'];key=(row['scenario'],row['seed'])
        if c not in groups or (c,key) in keys:raise ValueError('Unknown condition or duplicate trial')
        if row['success'] not in (True,False) or row['collision'] not in (True,False):
            raise ValueError('Unknown outcomes cannot be silently treated as failures or successes')
        keys[c,key]=True;groups[c].append(row)
    scenarios=[{(r['scenario'],r['seed']) for r in groups[c]} for c in conditions]
    if not all(s == scenarios[0] for s in scenarios) or not scenarios[0]:
        raise ValueError('A/B/C/D must contain matching scenarios and seeds, including failed trials')
    out={}
    for c,rows in groups.items():
        n=len(rows);success=sum(r['success'] for r in rows);collision=sum(r['collision'] for r in rows)
        def wilson(k):
            z=1.959963984540054;p=k/n;den=1+z*z/n
            centre=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
            return [centre-half,centre+half]
        measures={}
        for field in ('minimum_clearance_m','navigation_time_s','path_length_m','interventions'):
            values=[r[field] for r in rows]
            if any(v is None or not math.isfinite(v) or v<0 for v in values):
                raise ValueError('Incomplete trial measurement: '+field)
            measures[field]=dict(mean=float(np.mean(values)),std=float(np.std(values,ddof=1)) if n>1 else None)
        out[c]=dict(n=n,successes=success,collisions=collision,success_rate=success/n,
          collision_rate=collision/n,success_wilson95=wilson(success),collision_wilson95=wilson(collision),measures=measures)
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('jsonl',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    records=[json.loads(line) for line in a.jsonl.read_text().splitlines() if line.strip()]
    a.output.write_text(json.dumps(summarize(records),indent=2))
