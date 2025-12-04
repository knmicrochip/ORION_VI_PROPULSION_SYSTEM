# main.py
import tkinter as tk
from comms import MQTTHandler
from inputs import InputManager
from utils import LatencyEstimator
from gui import AppGUI

# Inicjalizacja głównych obiektów
root = tk.Tk()
root.title("ODrive Modular Control")
root.geometry("1200x800")

# Input Manager
input_mgr = InputManager()

# Latency
latency = LatencyEstimator()

# GUI (przekazujemy placeholder dla mqtt, bo mqtt potrzebuje callbacka do GUI)
# Rozwiązanie: stworzymy GUI, potem MQTT, potem przypiszemy MQTT do GUI
# Ale prościej: Przekażmy funkcję logowania później lub użyjmy wrappera.
# Tutaj zrobimy to prosto:

app = None # Placeholder

def log_wrapper(msg):
    if app: app.log(msg)
    else: print(msg)

mqtt_handler = MQTTHandler(log_wrapper)
app = AppGUI(root, mqtt_handler, input_mgr)

# Binds klawiatury globalne
root.bind("<KeyPress>", lambda e: input_mgr.handle_keyboard('press', e.keysym))
root.bind("<KeyRelease>", lambda e: input_mgr.handle_keyboard('release', e.keysym))
root.bind("<Escape>", lambda e: root.attributes('-fullscreen', False))

# Zmienne pętli
plot_counter = 0

def main_loop():
    global plot_counter
    
    # 1. Pobierz wejścia
    vel, steer, limit = input_mgr.get_control_values()
    
    # 2. Wyślij do ODrive
    mqtt_handler.send_velocity(vel, steer)
    latency.push_target(vel)
    
    # 3. Oblicz Lag
    meas_vel = mqtt_handler.measured_velocity
    lag = latency.estimate_lag(meas_vel)
    
    # 4. Aktualizuj GUI
    app.update(vel, steer, limit, lag)
    
    # Wykres rzadziej (co 4 klatki = ok. 200ms)
    plot_counter += 1
    if plot_counter % 4 == 0:
        app.update_plot_canvas()
        
    root.after(50, main_loop)

# START
if __name__ == "__main__":
    mqtt_handler.start()
    app._reset_joysticks_ui() # Odśwież listę po starcie GUI
    main_loop()
    root.mainloop()