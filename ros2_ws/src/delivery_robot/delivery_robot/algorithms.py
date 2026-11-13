"""Pure Python trajectory prediction and conservative obstacle logic."""
from dataclasses import dataclass
from math import hypot, isfinite, cos, sin, atan2


@dataclass
class Track:
    x: float
    y: float
    vx: float
    vy: float
    timestamp: float


class Tracker:
    """Lightweight nearest-neighbor tracker; not robust to occlusion/crossing."""
    def __init__(self, gate=1.2, max_age=0.8):
        self.gate = gate
        self.max_age = max_age
        self.tracks = {}
        self.next_id = 0

    def update(self, detections, now):
        if not isfinite(now) or any(not all(isfinite(v) for v in d) for d in detections):
            raise ValueError("Nonfinite observations")
        if any(now <= t.timestamp for t in self.tracks.values()):
            raise ValueError("Observations must advance in time")
        self.tracks = {i: t for i, t in self.tracks.items()
                       if 0 <= now - t.timestamp <= self.max_age}
        candidates = sorted((hypot(x-t.x, y-t.y), j, i)
                            for j, (x, y) in enumerate(detections)
                            for i, t in self.tracks.items()
                            if hypot(x-t.x, y-t.y) <= self.gate)
        used_d, used_t = set(), set()
        for _, j, i in candidates:
            if j in used_d or i in used_t:
                continue
            x, y = detections[j]
            t = self.tracks[i]
            dt = now - t.timestamp
            if dt > 1e-4:
                t.vx = (x-t.x)/dt
                t.vy = (y-t.y)/dt
            t.x, t.y, t.timestamp = x, y, now
            used_d.add(j)
            used_t.add(i)
        for j, (x, y) in enumerate(detections):
            if j not in used_d:
                self.tracks[self.next_id] = Track(x, y, 0., 0., now)
                self.next_id += 1

    def forecast(self, now, horizon=2., step=0.25):
        """(t_relative, x, y) for each track, grouped in blocks of fixed horizon."""
        if step <= 0 or horizon <= 0:
            raise ValueError('Horizon and step must be positive')
        out = []
        for track in self.tracks.values():
            age = now - track.timestamp
            if 0 <= age <= self.max_age:
                for k in range(1, int(horizon/step) + 1):
                    dt = step*k
                    out.append((dt, track.x + track.vx*(age+dt),
                                track.y + track.vy*(age+dt)))
        return out


def scan_clearance(ranges, angle_min, angle_increment, range_min, range_max):
    valid = []
    for index, value in enumerate(ranges):
        angle = angle_min + index*angle_increment
        angle = atan2(sin(angle), cos(angle))
        if isfinite(angle) and isfinite(value) and range_min <= value <= range_max:
            valid.append(value)
    return min(valid) if valid else None


def will_conflict(x, y, yaw, v, w, predictions, radius=0.85):
    for dt, px, py in predictions:
        if dt < 0:
            continue
        if abs(w) < 1e-6:
            rx, ry = x + v*dt*cos(yaw), y + v*dt*sin(yaw)
        else:
            rx = x + v/w*(sin(yaw+w*dt) - sin(yaw))
            ry = y - v/w*(cos(yaw+w*dt) - cos(yaw))
        if hypot(px-rx, py-ry) < radius:
            return True
    return False


def gate_velocity(v, w, clearance, pose, predictions):
    """Zero command on missing scan / obstacle / forecast collision."""
    values = [v, w, *pose] + [z for row in predictions for z in row]
    if (not all(isfinite(z) for z in values) or clearance is None
            or not isfinite(clearance) or clearance <= 0.65 or abs(v) > 0.5 or abs(w) > 1.0):
        return 0., 0.
    if will_conflict(*pose, v, w, predictions):
        return 0., 0.
    factor = min(1., max(0., (clearance-0.65)/0.60))
    return v*factor, w*factor
