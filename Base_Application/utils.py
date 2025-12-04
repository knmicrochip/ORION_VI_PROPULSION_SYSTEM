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
        # Przeszukiwanie historii w poszukiwaniu pasującej prędkości
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

class AppState:
    """Klasa przechowująca współdzielony stan aplikacji"""
    def __init__(self):
        # Dane pomiarowe
        self.measured_velocity = 0.0
        self.measured_position = 0.0
        self.start_position_offset = 0.0
        self.last_feedback_time = 0.0
        
        # Dane sterujące
        self.target_rps = 0.0
        self.steering_val = 0.0
        self.current_speed_limit = 10.0
        
        # Statusy
        self.mqtt_connected = False
        self.mqtt_status_text = "MQTT: Rozłączono"
        
        # Logi
        self.logs = [] # Lista do przechowywania logów dla GUI
        
        # Narzędzia
        self.latency_estimator = LatencyEstimator(maxlen=100)

    def log(self, message):
        self.logs.append(message)