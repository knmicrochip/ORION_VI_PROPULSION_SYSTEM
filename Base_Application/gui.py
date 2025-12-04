# gui.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import deque
import threading
import time
from config import *

class AppGUI:
    def __init__(self, root, mqtt_handler, input_manager):
        self.root = root
        self.mqtt = mqtt_handler
        self.input_mgr = input_manager
        
        # Dane wykresu
        self.plot_data_x = deque(maxlen=200)
        self.plot_data_target = deque(maxlen=200)
        self.plot_data_meas = deque(maxlen=200)
        self.start_time = time.time()
        self.start_pos_offset = 0.0

        self._setup_ui()

    def _setup_ui(self):
        self.root.configure(bg=BG_COLOR)
        
        # Layout Frames
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(fill="both", expand=True)
        
        self.left = tk.Frame(main_frame, bg=BG_COLOR, width=500)
        self.left.pack(side="left", fill="y", padx=10, pady=10)
        self.left.pack_propagate(False)
        
        self.center = tk.Frame(main_frame, bg=BG_COLOR)
        self.center.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        self.right = tk.Frame(main_frame, bg=BG_COLOR, width=400)
        self.right.pack(side="left", fill="y", padx=10, pady=10)
        self.right.pack_propagate(False)
        
        self._build_left_panel()
        self._build_center_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        # Joystick
        self.joy_frame = tk.LabelFrame(self.left, text="Joysticki", bg=BG_COLOR, fg=FG_COLOR)
        self.joy_frame.pack(fill="x", pady=5)
        tk.Button(self.joy_frame, text="⟳ RESET JOYSTICK", command=self._reset_joysticks_ui, 
                  bg=BTN_RESET_COLOR, fg="white").pack(fill="x", padx=5, pady=5)
        self.joy_lbl = tk.Label(self.joy_frame, text="...", bg=BG_COLOR, fg="#aaa")
        self.joy_lbl.pack()

        # Wykres
        plot_frame = tk.LabelFrame(self.left, text="Wykres Prędkości", bg=BG_COLOR, fg=FG_COLOR)
        plot_frame.pack(side="bottom", fill="both", expand=True, pady=(20, 0))
        
        self.fig = Figure(figsize=(4, 3), dpi=100, facecolor=BG_COLOR)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(BG_COLOR)
        self.ax.tick_params(colors='white')
        for spine in self.ax.spines.values(): spine.set_color('white')
        self.ax.grid(True, color='#444', linestyle='--')
        
        self.line_target, = self.ax.plot([], [], color='#00ffff', linewidth=2, linestyle='--') 
        self.line_meas, = self.ax.plot([], [], color='#00ff00', linewidth=2) 
        
        self.canvas_plot = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas_plot.get_tk_widget().pack(fill="both", expand=True)

    def _build_center_panel(self):
        # Zegar
        gauge_frame = tk.LabelFrame(self.center, text="Wskaźniki", bg=BG_COLOR, fg=FG_COLOR)
        gauge_frame.pack(pady=10, fill="both")
        self.gauge_canvas = tk.Canvas(gauge_frame, width=400, height=300, bg=BG_COLOR, highlightthickness=0)
        self.gauge_canvas.pack(pady=10)
        
        self.lbl_target = tk.Label(gauge_frame, text="Target: 0.0", bg=BG_COLOR, fg=FG_COLOR, font=("Arial", 24, "bold"))
        self.lbl_target.pack()
        self.lbl_steer = tk.Label(gauge_frame, text="Steering: 0.0", bg=BG_COLOR, fg="#FFAA00", font=("Arial", 16))
        self.lbl_steer.pack()

        # Feedback
        fb_frame = tk.LabelFrame(self.center, text="Feedback", bg=BG_COLOR, fg="#00ff00")
        fb_frame.pack(pady=20, fill="x")
        
        self.lbl_meas_vel = tk.Label(fb_frame, text="RPS: 0.00", bg=BG_COLOR, fg="#00ff00", font=("Consolas", 18))
        self.lbl_meas_vel.pack(anchor="w", padx=10)
        
        self.lbl_speed_kmh = tk.Label(fb_frame, text="0.0 km/h", bg=BG_COLOR, fg="#ff00ff", font=("Consolas", 20, "bold"))
        self.lbl_speed_kmh.pack(anchor="w", padx=10)
        
        self.lbl_dist = tk.Label(fb_frame, text="Dystans: 0.00 m", bg=BG_COLOR, fg="white", font=("Consolas", 14))
        self.lbl_dist.pack(anchor="w", padx=10)
        tk.Button(fb_frame, text="RESET TRIP", command=self._reset_trip, bg="#444", fg="white").pack(anchor="w", padx=10)
        
        self.lbl_lag = tk.Label(fb_frame, text="Lag: -- ms", bg=BG_COLOR, fg="#aaa", font=("Consolas", 14))
        self.lbl_lag.pack(anchor="w", padx=10, pady=10)

    def _build_right_panel(self):
        self.mqtt_status = tk.StringVar(value="MQTT: Rozłączono")
        tk.Label(self.right, textvariable=self.mqtt_status, bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w")
        
        self.console = scrolledtext.ScrolledText(self.right, bg="#222", fg="#0f0", height=15, font=("Consolas", 9))
        self.console.pack(fill="both", pady=5)

        cmd_frame = tk.LabelFrame(self.right, text="Komendy", bg=BG_COLOR, fg=FG_COLOR)
        cmd_frame.pack(fill="x", side="bottom", pady=20)
        
        self.btn_start = tk.Button(cmd_frame, text="★ FULL START ★", command=self._run_full_start, bg=BTN_FULL_START_COLOR, fg="white")
        self.btn_start.pack(fill="x", padx=5, pady=5)
        
        cmds = [("Kalibracja", "calibrate"), ("Closed Loop", "closed_loop"), ("Vel Mode", "set_vel_mode")]
        for name, cmd in cmds:
            tk.Button(cmd_frame, text=name, command=lambda c=cmd: self.mqtt.send_cmd(c), bg=BTN_CMD_COLOR, fg="white").pack(fill="x", pady=2)
            
        tk.Button(cmd_frame, text="DUMP ERRORS", command=lambda: self.mqtt.send_cmd("dump_errors"), bg=BTN_DUMP_COLOR, fg="white").pack(fill="x", pady=5)
        tk.Button(cmd_frame, text="REBOOT", command=lambda: self.mqtt.send_cmd("reboot_odrive"), bg=BTN_REBOOT_COLOR, fg="white").pack(fill="x", pady=2)

    # --- GUI LOGIC ---
    def log(self, msg):
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)
        if "Połączono" in msg: self.mqtt_status.set("MQTT: POŁĄCZONO")

    def _reset_joysticks_ui(self):
        joys = self.input_mgr.reset_joysticks()
        names = [j.get_name()[:15] for j in joys]
        self.joy_lbl.config(text="\n".join(names) if names else "BRAK")

    def _reset_trip(self):
        self.start_pos_offset = self.mqtt.measured_position

    def _draw_gauge(self, val, max_v, limit_v):
        c = self.gauge_canvas
        c.delete("all")
        cx, cy, r = 200, 150, 130
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=0, extent=180, style="arc", outline="#333", width=25)
        limit_angle = (limit_v / max_v) * 180
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=180, extent=-limit_angle, style="arc", outline="#665500", width=25)
        
        val_clamped = max(-max_v, min(max_v, val))
        draw_angle = (val_clamped / max_v) * 90 
        color = "#00ff00" if val >= 0 else "#ff5500"
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=90, extent=-draw_angle, style="arc", outline=color, width=25)
        c.create_text(cx, cy, text=f"{val:.1f}", fill="white", font=("Arial", 36, "bold"))

    def _run_full_start(self):
        def sequence():
            self.mqtt.send_cmd("calibrate")
            for i in range(10, 0, -1):
                self.btn_start.config(text=f"Czekaj {i}s...", state="disabled")
                time.sleep(1)
            self.mqtt.send_cmd("closed_loop")
            time.sleep(0.1)
            self.mqtt.send_cmd("set_vel_mode")
            time.sleep(0.1)
            self.mqtt.send_cmd("set_ramp_mode")
            self.btn_start.config(text="★ FULL START ★", state="normal")
            self.log("Auto-start zakończony.")
        threading.Thread(target=sequence, daemon=True).start()

    def update(self, target_vel, target_steer, limit_vel, lag_ms):
        # Aktualizacja danych wykresu
        now = time.time() - self.start_time
        meas_vel = self.mqtt.measured_velocity
        meas_pos = self.mqtt.measured_position
        
        self.plot_data_x.append(now)
        self.plot_data_target.append(target_vel)
        self.plot_data_meas.append(meas_vel)
        
        # Odświeżanie widgetów
        self.lbl_target.config(text=f"Target: {target_vel:.2f}")
        self.lbl_steer.config(text=f"Steering: {target_steer:.2f}")
        self.lbl_meas_vel.config(text=f"RPS: {meas_vel:.2f}")
        
        speed_kmh = (meas_vel * DISTANCE_PER_MOTOR_REV) * 3.6
        self.lbl_speed_kmh.config(text=f"{speed_kmh:.1f} km/h")
        
        dist = (meas_pos - self.start_pos_offset) * DISTANCE_PER_MOTOR_REV
        self.lbl_dist.config(text=f"Dystans: {dist:.2f} m")
        
        if lag_ms is not None:
            self.lbl_lag.config(text=f"Lag: {int(lag_ms)} ms", fg="red" if lag_ms > 500 else "green")
        
        self._draw_gauge(target_vel, ABSOLUTE_MAX_LIMIT, limit_vel)

    def update_plot_canvas(self):
        if len(self.plot_data_x) > 1:
            self.line_target.set_data(self.plot_data_x, self.plot_data_target)
            self.line_meas.set_data(self.plot_data_x, self.plot_data_meas)
            self.ax.set_xlim(min(self.plot_data_x), max(self.plot_data_x) + 0.1)
            self.ax.set_ylim(-ABSOLUTE_MAX_LIMIT*1.1, ABSOLUTE_MAX_LIMIT*1.1)
            self.canvas_plot.draw_idle()