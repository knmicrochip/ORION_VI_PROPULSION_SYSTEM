import paho.mqtt.client as mqtt
import json
import time
import config

class MqttManager:
    def __init__(self, app_state):
        self.client = None
        self.state = app_state

    def connect(self):
        self.state.log("--- Inicjalizacja MQTT ---")
        try:
            # Używamy dokładnie tej samej wersji API co w Twoim pliku
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            
            self.state.log(f"Łączenie z {config.BROKER_ADDRESS}...")
            self.client.connect(config.BROKER_ADDRESS, config.BROKER_PORT)
            self.client.loop_start()
            
        except Exception as e:
            self.state.mqtt_status_text = "MQTT: Błąd"
            self.state.log(f"Błąd krytyczny połączenia: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.state.mqtt_connected = True
            self.state.mqtt_status_text = "MQTT: POŁĄCZONO"
            client.subscribe(config.TOPIC_FEEDBACK)
            self.state.log(">> Połączono z brokerem (RC=0).")
        else:
            self.state.mqtt_status_text = f"MQTT: Błąd {rc}"
            self.state.log(f"Błąd połączenia, kod: {rc}")

    def _on_message(self, client, userdata, msg):
        self.state.last_feedback_time = time.time()
        try:
            # Dekodowanie JSON dokładnie tak jak w Twoim pliku
            payload = json.loads(msg.payload.decode())
            
            if "error" in payload:
                self.state.log(f"!! ERROR: {payload['error']}")

            # Pobieranie v_meas i p_meas
            self.state.measured_velocity = payload.get("v_meas", 0.0)
            self.state.measured_position = payload.get("p_meas", 0.0)
            
            # Lag estimator (jeśli używasz utils.py z poprzedniej wersji)
            self.state.latency_estimator.estimate_lag(self.state.measured_velocity)
            
        except json.JSONDecodeError:
            raw = msg.payload.decode()
            self.state.log(f"MSG (RAW): {raw}")
        except Exception as e:
            # Ciche ignorowanie błędów parsowania, żeby nie spamować konsoli
            pass

    def send_drive_command(self):
        """Wysyła ramkę sterującą JSON: velocity + steering"""
        if self.client and self.state.mqtt_connected:
            # Dokładnie ta sama struktura JSON co w aplikacja_new_with_servo.py
            payload = {
                "velocity": round(self.state.target_rps, 3),
                "steering": round(self.state.steering_val, 3)
            }
            try:
                self.client.publish(config.TOPIC_SET_VELOCITY, json.dumps(payload))
                self.state.latency_estimator.push_target(self.state.target_rps)
            except Exception as e:
                self.state.log(f"Błąd wysyłania: {e}")

    def send_cmd(self, cmd):
        """Wysyła proste komendy tekstowe (calibrate, closed_loop itp.)"""
        if self.client and self.state.mqtt_connected:
            self.client.publish(config.TOPIC_CMD, cmd)
            self.state.log(f">> CMD: {cmd}")