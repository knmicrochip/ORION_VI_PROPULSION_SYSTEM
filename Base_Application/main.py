import sys
import os
import multiprocessing # <--- DODAJ IMPORT

# === FIX 1: Naprawa błędu Matplotlib (File already exists) ===
# Ten kod musi być PRZED importem gui i matplotlib!
if getattr(sys, 'frozen', False):
    import tempfile
    # Ustawiamy cache matplotlib w folderze tymczasowym systemu
    # Dzięki temu nie próbuje pisać w zablokowanych folderach PyInstallera
    config_dir = os.path.join(tempfile.gettempdir(), 'orion_mpl_config')
    os.environ['MPLCONFIGDIR'] = config_dir
    try:
        os.makedirs(config_dir, exist_ok=True)
    except Exception:
        pass
# =============================================================
import tkinter as tk
from utils import AppState
from inputs import InputManager
from comms import MqttManager
from gui import DashboardGUI


def main():
    # 1. Inicjalizacja Głównego Okna
    root = tk.Tk()
    root.title("ODrive Control Modular")
    root.attributes('-fullscreen', True)
    
    # 2. Inicjalizacja Stanu i Modułów
    app_state = AppState()
    input_manager = InputManager()
    mqtt_manager = MqttManager(app_state)
    
    # 3. Inicjalizacja GUI
    gui = DashboardGUI(root, app_state, input_manager, mqtt_manager)
    
    # 4. Bindings (Klawiatura musi być podpięta pod root)
    def on_key_press(event):
        if event.keysym.lower() == 'escape':
            root.attributes('-fullscreen', False)
            root.geometry("1200x800")
        else:
            input_manager.handle_keyboard('press', event.keysym)

    def on_key_release(event):
        input_manager.handle_keyboard('release', event.keysym)

    root.bind("<KeyPress>", on_key_press)
    root.bind("<KeyRelease>", on_key_release)

    # 5. Start MQTT
    mqtt_manager.connect()
    
    # 6. Pętla Główna
    def main_loop():
        # A. Odczyt wejść (Joystick/Klawiatura) -> Aktualizacja AppState
        input_manager.update(app_state)
        
        # B. Wysłanie komend do ODrive przez MQTT
        mqtt_manager.send_drive_command()
        
        # C. Odświeżenie GUI (Wykresy, Labele)
        gui.update_interface()
        
        # D. Planowanie kolejnej klatki (50ms = 20 FPS odświeżania logiki)
        root.after(50, main_loop)

    gui.refresh_joysticks()
    main_loop()
    root.mainloop()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()