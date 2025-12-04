# comms.py
import paho.mqtt.client as mqtt
import json
import time
from config import *

class MQTTHandler:
    def __init__(self, log_callback):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.log_callback = log_callback # Funkcja do logowania w GUI
        self.connected = False
        
        # Dane odebrane
        self.measured_velocity = 0.0
        self.measured_position = 0.0
        self.last_feedback_time = 0.0
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def start(self):
        try:
            self.client.connect(BROKER_ADDRESS, BROKER_PORT)
            self.client.loop_start()
        except Exception as e:
            self.log_callback(f"MQTT Error: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.log_callback(">> MQTT Połączono.")
            self.client.subscribe(TOPIC_FEEDBACK)
        else:
            self.log_callback(f"MQTT Connect Fail rc={rc}")

    def _on_message(self, client, userdata, msg):
        self.last_feedback_time = time.time()
        try:
            payload = json.loads(msg.payload.decode())
            if "error" in payload:
                self.log_callback(f"!! ERROR: {payload['error']}")
            
            self.measured_velocity = payload.get("v_meas", 0.0)
            self.measured_position = payload.get("p_meas", 0.0)
            
        except json.JSONDecodeError:
            self.log_callback(f"MSG: {msg.payload.decode()}")
        except Exception:
            pass

    def send_velocity(self, velocity, steering):
        if self.connected:
            payload = {
                "velocity": round(velocity, 3),
                "steering": round(steering, 3)
            }
            self.client.publish(TOPIC_SET_VELOCITY, json.dumps(payload))

    def send_cmd(self, cmd):
        if self.connected:
            self.client.publish(TOPIC_CMD, cmd)
            self.log_callback(f">> CMD: {cmd}")