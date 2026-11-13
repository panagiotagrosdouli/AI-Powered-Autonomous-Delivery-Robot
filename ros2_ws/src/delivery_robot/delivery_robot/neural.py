"""Optional trained checkpoint adapter. No synthetic model is accepted by default."""
from collections import deque

class NeuralAdapter:
    def __init__(self,path,allow_synthetic=False):
        import torch
        from research.models import Forecaster
        self.torch=torch
        checkpoint=torch.load(path,map_location='cpu',weights_only=True)
        if checkpoint['data_kind'] != 'REAL RECORDED PEDESTRIANS' and not allow_synthetic:
            raise ValueError('Runtime refuses synthetic/unclassified training checkpoints')
        self.obs=checkpoint['obs'];self.pred=checkpoint['pred'];self.step=checkpoint['sample_interval_seconds']
        if self.obs<2 or self.pred<1 or self.step<=0:raise ValueError('Invalid checkpoint metadata')
        self.model=Forecaster(checkpoint['kind'],self.pred)
        self.model.load_state_dict(checkpoint['state_dict']);self.model.eval()
        self.history={}

    def update(self,tracks):
        self.history={i:h for i,h in self.history.items() if i in tracks}
        for i,t in tracks.items():
            h=self.history.setdefault(i,deque(maxlen=self.obs))
            if h:
                dt=t.timestamp-h[-1][0]
                if dt<self.step*.8:continue
                if dt>self.step*1.2:h.clear()
            h.append((t.timestamp,t.x,t.y))

    def forecast(self,tracks,now):
        result={}
        with self.torch.no_grad():
            for i,t in tracks.items():
                if not 0<=now-t.timestamp<=.6:continue
                h=self.history.get(i,[])
                if len(h)<self.obs:return None  # fail closed while collecting history
                points=self.torch.tensor([[[x,y] for _,x,y in h]],dtype=self.torch.float32)
                forecast=self.model(points)[0]
                if not self.torch.isfinite(forecast).all():raise ValueError('Nonfinite model prediction')
                age=now-h[-1][0]
                result[i]=[(k*self.step-age,float(x),float(y)) for k,(x,y) in enumerate(forecast,1) if k*self.step>age]
        return result
