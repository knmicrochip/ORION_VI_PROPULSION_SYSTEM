import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from collections import deque

# Matplotlib
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import config

class DashboardGUI:
    def __init__(self, root, app_state, input_manager, mqtt_manager):
        self.root = root
        self.state = app_state
        self.input_manager = input_manager
        self.mqtt_manager = mqtt_manager
        
        # Dane do wykresu
        self.plot_data_x = deque(maxlen=200)
        self.plot_data_target = deque(maxlen=200)
        self.plot_data_meas = deque(maxlen=200)
        self.start_time = time.time()
        self.plot_counter = 0

        self.setup_ui()
        
    def setup_ui(self):
        self.root.configure(bg=config.BG_COLOR)
        # Layout Frames
        self.main_frame = tk.Frame(self.root, bg=config.BG_COLOR)
        self.main_frame.pack(fill="both", expand=True)

        self.left_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR, width=500)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)
        self.left_frame.pack_propagate(False)

        self.center_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR)
        self.center_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.right_frame = tk.Frame(self.main_frame, bg=config.BG_COLOR, width=400)
        self.right_frame.pack(side="left", fill="y", padx=10, pady=10)
        self.right_frame.pack_propagate(False)

        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        # Joysticki
        self.joy_container = tk.Frame(self.left_frame, bg=config.BG_COLOR)
        self.joy_container.pack(side="top", fill="x")
        self.joystick_list_frame = tk.Frame(self.joy_container, bg=config.BG_COLOR)
        
        tk.Button(self.joy_container, text="⟳ RESET JOYSTICK", command=self.refresh_joysticks, 
                  bg=config.BTN_RESET_COLOR, fg="white", font=("Arial", 10, "bold")).pack(fill="x", pady=(0,10))
        self.joystick_list_frame.pack(fill="both", expand=True)

        # Instrukcja
        instr = tk.LabelFrame(self.left_frame, text="Klawiatura", bg=config.BG_COLOR, fg="#ccc")
        instr.pack(fill="x", pady=10)
        tk.Label(instr, text="[W]/[S] - Przód/Tył | [R]/[F] - Limit", bg=config.BG_COLOR, fg="white", font=("Arial", 10, "bold")).pack()
        tk.Label(instr, text="[ESC] - Zamknij fullscreen", bg=config.BG_COLOR, fg="#888").pack()

        # Wykres
        self.plot_frame = tk.LabelFrame(self.left_frame, text="Wykres Prędkości", bg=config.BG_COLOR, fg=config.FG_COLOR)
        self.plot_frame.pack(side="bottom", fill="both", expand=True, pady=(20, 0))
        
        self.fig = Figure(figsize=(4, 3), dpi=100, facecolor=config.BG_COLOR)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(config.BG_COLOR)
        self.ax.tick_params(colors='white')
        for spine in self.ax.spines.values(): spine.set_color('white')
        self.ax.grid(True, color='#444', linestyle='--')
        
        self.line_target, = self.ax.plot([], [], color='#00ffff', label='Target', linestyle='--')
        self.line_meas, = self.ax.plot([], [], color='#00ff00', label='Measured')
        self.ax.legend(loc="upper right", facecolor=config.BG_COLOR, labelcolor='white', framealpha=0.5)
        
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas_plot.get_tk_widget().pack(fill="both", expand=True)

    def _build_center_panel(self):
        # Gauge (Zegary)
        gauge_frame = tk.LabelFrame(self.center_frame, text="Wskaźniki", bg=config.BG_COLOR, fg=config.FG_COLOR)
        gauge_frame.pack(pady=10, fill="both")
        self.gauge_canvas = tk.Canvas(gauge_frame, width=400, height=300, bg=config.BG_COLOR, highlightthickness=0)
        self.gauge_canvas.pack(pady=10)
        
        self.lbl_target = tk.Label(gauge_frame, text="Target: 0.0 RPS", bg=config.BG_COLOR, fg="white", font=("Arial", 24, "bold"))
        self.lbl_target.pack()
        self.lbl_steering = tk.Label(gauge_frame, text="Steering: 0.00", bg=config.BG_COLOR, fg="#FFAA00", font=("Arial", 16))
        self.lbl_steering.pack(pady=(0, 10))

        # Feedback Frame
        fb_frame = tk.LabelFrame(self.center_frame, text="Feedback & Diagnostyka", bg=config.BG_COLOR, fg="#00ff00")
        fb_frame.pack(pady=20, fill="x", padx=10)
        
        # 1. RPS (Dodano)
        self.lbl_meas_vel = tk.Label(fb_frame, text="RPS: 0.00", bg=config.BG_COLOR, fg="#00ff00", font=("Consolas", 18))
        self.lbl_meas_vel.pack(anchor="w", padx=10, pady=2)

        # 2. Kontener prędkości (km/h i m/s obok siebie)
        speed_container = tk.Frame(fb_frame, bg=config.BG_COLOR)
        speed_container.pack(anchor="w", padx=10, pady=2)
        
        self.lbl_kmh = tk.Label(speed_container, text="0.0 km/h", bg=config.BG_COLOR, fg="#ff00ff", font=("Consolas", 20, "bold"))
        self.lbl_kmh.pack(side="left", padx=(0, 20))
        
        self.lbl_ms = tk.Label(speed_container, text="0.00 m/s", bg=config.BG_COLOR, fg="#ff88ff", font=("Consolas", 14))
        self.lbl_ms.pack(side="left")

        # 3. Pozycja
        self.lbl_pos = tk.Label(fb_frame, text="Pozycja: 0.00 obr", bg=config.BG_COLOR, fg="#00ccff", font=("Consolas", 18))
        self.lbl_pos.pack(anchor="w", padx=10, pady=5)
        
        # 4. Dystans i Reset
        dist_container = tk.Frame(fb_frame, bg=config.BG_COLOR)
        dist_container.pack(anchor="w", padx=10, pady=5)
        
        self.lbl_dist = tk.Label(dist_container, text="Dystans: 0.00 m", bg=config.BG_COLOR, fg="white", font=("Consolas", 18))
        self.lbl_dist.pack(side="left")
        
        tk.Button(dist_container, text="[RESET]", command=self.reset_trip, bg="#444", fg="white", font=("Arial", 10)).pack(side="left", padx=10)
        
        tk.Frame(fb_frame, height=1, bg="#444").pack(fill="x", padx=5, pady=5)
        
        # 5. Diagnostyka (Packet Age + Lag)
        self.lbl_packet_age = tk.Label(fb_frame, text="Sieć (Packet Age): -- ms", bg=config.BG_COLOR, fg="#aaaaaa", font=("Consolas", 11))
        self.lbl_packet_age.pack(anchor="w", padx=10)

        self.lbl_lag = tk.Label(fb_frame, text="Lag: -- ms", bg=config.BG_COLOR, fg="#aaaaaa", font=("Consolas", 16, "bold"))
        self.lbl_lag.pack(anchor="w", padx=10, pady=(5,10))

    def _build_right_panel(self):
        self.lbl_mqtt_status = tk.Label(self.right_frame, text="MQTT: Rozłączono", bg=config.BG_COLOR, fg=config.FG_COLOR, font=("Arial", 12))
        self.lbl_mqtt_status.pack(anchor="w")
        
        self.console = scrolledtext.ScrolledText(self.right_frame, bg="#222", fg="#0f0", height=15, font=("Consolas", 10))
        self.console.pack(fill="both", expand=True, pady=5)
        
        cmd_frame = tk.LabelFrame(self.right_frame, text="Polecenia ODrive", bg=config.BG_COLOR, fg=config.FG_COLOR)
        cmd_frame.pack(fill="x", side="bottom", pady=20)
        
        self.btn_full_start = tk.Button(cmd_frame, text="★ FULL START (AUTO) ★", command=self.run_full_start, 
                                        bg=config.BTN_FULL_START_COLOR, fg="white", height=2, font=("Arial", 11, "bold"))
        self.btn_full_start.pack(fill="x", padx=10, pady=(10, 20))
        
        tk.Button(cmd_frame, text="1. KALIBRACJA", command=lambda: self.mqtt_manager.send_cmd("calibrate"), 
                  bg="#AA8800", fg="white", height=1).pack(fill="x", padx=10, pady=2)
        
        tk.Button(cmd_frame, text="2. CLOSED LOOP", command=lambda: self.mqtt_manager.send_cmd("closed_loop"), 
                  bg="#006600", fg="white", height=1).pack(fill="x", padx=10, pady=2)
        
        tk.Button(cmd_frame, text="3. TRYB VELOCITY", command=lambda: self.mqtt_manager.send_cmd("set_vel_mode"), 
                  bg="#004488", fg="white", height=1).pack(fill="x", padx=10, pady=2)
        
        tk.Button(cmd_frame, text="4. RAMP MODE", command=lambda: self.mqtt_manager.send_cmd("set_ramp_mode"), 
                  bg="#550088", fg="white", height=1).pack(fill="x", padx=10, pady=2)

        tk.Button(cmd_frame, text="DUMP ERRORS (odrv0)", command=lambda: self.mqtt_manager.send_cmd("dump_errors"), 
                  bg=config.BTN_DUMP_COLOR, fg="white", height=1, font=("Arial", 10, "bold")).pack(fill="x", padx=10, pady=(10, 2))
        
        tk.Button(cmd_frame, text="⚠ REBOOT ODRIVE", command=lambda: self.mqtt_manager.send_cmd("reboot_odrive"), 
                  bg=config.BTN_REBOOT_COLOR, fg="white", height=1, font=("Arial", 10, "bold")).pack(fill="x", padx=10, pady=(10, 2))

    def refresh_joysticks(self):
        joysticks = self.input_manager.scan_joysticks()
        for widget in self.joystick_list_frame.winfo_children():
            widget.destroy()
        if not joysticks:
            tk.Label(self.joystick_list_frame, text="BRAK JOYSTICKA (Użyj Klawiatury)", bg=config.BG_COLOR, fg="yellow").pack()
        for i, joy in enumerate(joysticks):
            joy_name = joy.get_name()[:15]
            tk.Label(self.joystick_list_frame, text=f"Joy {i}: {joy_name}", bg=config.BG_COLOR, fg="white").pack(anchor="w")

    def reset_trip(self):
        self.state.start_position_offset = self.state.measured_position
        self.lbl_dist.config(text="Dystans: 0.00 m")

    def run_full_start(self):
        threading.Thread(target=self._full_start_thread, daemon=True).start()

    def _full_start_thread(self):
        self.state.log("\n=== FULL START SEQUENCE ===")
        self.mqtt_manager.send_cmd("calibrate")
        
        self.btn_full_start.config(state="disabled", bg="#555555")
        for i in range(10, 0, -1):
            self.root.after(0, lambda t=i: self.btn_full_start.config(text=f"CZEKAJ: {t}s..."))
            time.sleep(1)
        
        self.root.after(0, lambda: self.btn_full_start.config(text="KONFIGURACJA..."))
        self.mqtt_manager.send_cmd("closed_loop")
        time.sleep(0.1)
        self.mqtt_manager.send_cmd("set_vel_mode")
        time.sleep(0.1)
        self.mqtt_manager.send_cmd("set_ramp_mode")
        
        self.state.log("=== FULL START ZAKOŃCZONY ===\n")
        self.root.after(0, lambda: self.btn_full_start.config(text="★ FULL START (AUTO) ★", state="normal", bg=config.BTN_FULL_START_COLOR))

    def update_interface(self):
        # 1. Update Labels (Target, Steering, Status)
        self.lbl_target.config(text=f"Target: {self.state.target_rps:.2f} RPS")
        self.lbl_steering.config(text=f"Steering: {self.state.steering_val:.2f}")
        self.lbl_mqtt_status.config(text=self.state.mqtt_status_text)
        
        # 2. Update Feedback (RPS, km/h, m/s)
        meas_rps = self.state.measured_velocity
        speed_ms = meas_rps * config.DISTANCE_PER_MOTOR_REV
        speed_kmh = speed_ms * 3.6
        
        self.lbl_meas_vel.config(text=f"RPS: {meas_rps:.2f}")     # <--- DODANO
        self.lbl_kmh.config(text=f"{speed_kmh:.1f} km/h")
        self.lbl_ms.config(text=f"{speed_ms:.2f} m/s")           # <--- DODANO
        
        self.lbl_pos.config(text=f"Pozycja: {self.state.measured_position:.2f} obr")
        
        trip_turns = self.state.measured_position - self.state.start_position_offset
        trip_distance_m = trip_turns * config.DISTANCE_PER_MOTOR_REV
        self.lbl_dist.config(text=f"Dystans: {trip_distance_m:.2f} m")

        # 3. Packet Age
        if self.state.last_feedback_time > 0:
            diff_ms = (time.time() - self.state.last_feedback_time) * 1000.0
            self.lbl_packet_age.config(text=f"Sieć (Packet Age): {int(diff_ms)} ms")
            if diff_ms < 200: self.lbl_packet_age.config(fg="#88ff88")
            elif diff_ms < 500: self.lbl_packet_age.config(fg="orange")
            else: self.lbl_packet_age.config(fg="red")
        else:
            self.lbl_packet_age.config(text="Sieć: Brak danych", fg="grey")

        # 4. Lag
        lag = self.state.latency_estimator.estimate_lag(self.state.measured_velocity)
        if lag is not None:
            self.lbl_lag.config(text=f"Lag: {int(lag)} ms")
            if lag < 300: self.lbl_lag.config(fg="#00ff00")
            elif lag < 600: self.lbl_lag.config(fg="orange")
            else: self.lbl_lag.config(fg="red")
        else:
            if abs(self.state.measured_velocity) < 0.5:
                self.lbl_lag.config(text="Lag: (Stop)", fg="#555")

        # Console logs
        while self.state.logs:
            msg = self.state.logs.pop(0)
            self.console.insert(tk.END, msg + "\n")
            self.console.see(tk.END)

        # Draw Gauge
        self._draw_gauge(self.state.target_rps)

        # Update Plot Data
        ct = time.time() - self.start_time
        self.plot_data_x.append(ct)
        self.plot_data_target.append(self.state.target_rps)
        self.plot_data_meas.append(self.state.measured_velocity)

        if self.plot_counter % config.PLOT_SKIP_FRAMES == 0 and len(self.plot_data_x) > 1:
            self.line_target.set_data(self.plot_data_x, self.plot_data_target)
            self.line_meas.set_data(self.plot_data_x, self.plot_data_meas)
            self.ax.set_xlim(min(self.plot_data_x), max(self.plot_data_x) + 0.1)
            limit = config.ABSOLUTE_MAX_LIMIT * 1.1
            self.ax.set_ylim(-limit, limit)
            self.canvas_plot.draw_idle()
        
        self.plot_counter += 1

    def _draw_gauge(self, val):
        self.gauge_canvas.delete("all")
        cx, cy, r = 200, 150, 130
        max_v = config.ABSOLUTE_MAX_LIMIT
        
        self.gauge_canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=0, extent=180, style="arc", outline="#333", width=25)
        limit_angle = (self.state.current_speed_limit / max_v) * 180
        self.gauge_canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=180, extent=-limit_angle, style="arc", outline="#665500", width=25)
        val_clamped = max(-max_v, min(max_v, val))
        draw_angle = (val_clamped / max_v) * 90 
        color = "#00ff00" if val >= 0 else "#ff5500"
        self.gauge_canvas.create_arc(cx-r, cy-r, cx+r, cy+r, start=90, extent=-draw_angle, style="arc", outline=color, width=25)
        self.gauge_canvas.create_text(cx, cy-20, text=f"{val:.1f}", fill="white", font=("Arial", 36, "bold"))
        self.gauge_canvas.create_text(cx, cy+25, text=f"Max Limit: {self.state.current_speed_limit:.1f} RPS", fill="#888", font=("Arial", 12))