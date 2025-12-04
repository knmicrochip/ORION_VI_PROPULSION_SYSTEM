# utils.py
import time
from collections import deque

class LatencyEstimator:
    def __init__(self, maxlen=50):
        self.history = deque(maxlen=maxlen)
    
    def push_target(self, target_vel):
        self.history.append((time.time(), target_vel))
        
    def estimate_lag(self, current_measured_vel):
        if abs(current_measured_vel) < 0.5:
            return None
        best_time = None
        min_diff = float('inf')
        for t_stamp, t_vel in reversed(self.history):
            diff = abs(t_vel - current_measured_vel)
            if diff < min_diff:
                min_diff = diff
                best_time = t_stamp
            if diff > min_diff + 2.0: 
                break
        if best_time:
            lag_seconds = time.time() - best_time
            return lag_seconds * 1000.0 
        return None