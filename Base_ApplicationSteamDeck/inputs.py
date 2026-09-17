# inputs.py
import pygame
import config
import time
import pygame._sdl2.controller


class InputManager:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        # Gamepad API (SDL GameController) - normalizuje różne pady (Xbox,
        # Steam Deck, Titan itd.) do wspólnego schematu osi/przycisków,
        # dzięki czemu nie musimy już rozpoznawać ich po GUID.
        # WYJĄTEK: Logitech to drążek (flight stick), nie gamepad - SDL go nie
        # mapuje na standardowy schemat, więc obsługujemy go osobno przez
        # surowe pygame.joystick, tak jak dotychczas.
        pygame._sdl2.controller.init()

        self.gamepads = []
        self.flight_stick = None
        self.scan_devices()

        # Zmienne klawiatury
        self.key_throttle = 0.0
        self.key_steering = 0.0
        self.key_max_limit = 10.0

        # Nowa zmienna: zapamiętuje limit ustawiony przez krzyżak/strzałki na padzie/drążku
        self.pad_max_limit = 10.0

    def scan_devices(self):
        """Wykrywa podłączone gamepady (SDL GameController) oraz drążek Logitech (surowy joystick)."""
        self.gamepads = []
        self.flight_stick = None

        pygame._sdl2.controller.quit()
        pygame.joystick.quit()
        pygame.joystick.init()
        pygame._sdl2.controller.init()
        pygame.event.clear()

        # Gamepady - przez znormalizowane API SDL GameController
        count = pygame._sdl2.controller.get_count()
        print(f"count:  {count}")
        for i in range(count):
            try:
                if pygame._sdl2.controller.is_controller(i):
                    gp = pygame._sdl2.controller.Controller(i)
                    gp.init()
                    self.gamepads.append(gp)
            except pygame.error:
                # Urządzenie nierozpoznane jako gamepad przez SDL (brak mapowania)
                pass

        # Drążek Logitech - przez surowe API joystick (nie jest gamepadem)
        joy_count = pygame.joystick.get_count()
        for i in range(joy_count):
            try:
                joy = pygame.joystick.Joystick(i)
                joy.init()
                if joy.get_guid() == config.LOGITECH_GUID:
                    self.flight_stick = joy
            except pygame.error:
                pass

        return self.gamepads

    def handle_keyboard(self, event_type, key_code):
        """Metoda wywoływana z GUI przy zdarzeniach klawiatury"""
        k = key_code.lower()

        if event_type == 'press':
            if k == 'w': self.key_throttle = 1.0
            elif k == 's': self.key_throttle = -1.0
            elif k == 'r': self.key_max_limit = min(config.ABSOLUTE_MAX_LIMIT, self.key_max_limit + 1.0)
            elif k == 'f': self.key_max_limit = max(1.0, self.key_max_limit - 1.0)
            elif k == 'a': self.key_steering = 1.0 
            elif k == 'd': self.key_steering = -1.0

        elif event_type == 'release':
            if k in ['w', 's', 'a', 'd']: 
                self.key_throttle = 0.0
                self.key_steering = 0.0

    def _handle_mode_toggle(self, app_state):
        """Wspólna logika przycisku 'A' / button 0 (Tryb Obrotu)."""
        # ZABEZPIECZENIE: Zmiana trybu tylko w spoczynku
        if abs(app_state.target_rps) < 0.1:
            if app_state.drive_mode == 1:
                app_state.drive_mode = 2
                app_state.mode_switch_time = time.time()
                app_state.log(">>> TRYB JAZDY: OBRÓT W MIEJSCU (Czekaj na serwa) <<<")
            else:
                app_state.drive_mode = 1
                app_state.mode_switch_time = time.time()
                app_state.log(">>> TRYB JAZDY: NORMALNY <<<")
        else:
            app_state.log("!!! ODMOWA ZMIANY TRYBU: Najpierw zatrzymaj łazika !!!")

    def _handle_lock_toggle(self, app_state):
        """Wspólna logika przycisku R3 / button 9 (Blokada bezpieczeństwa)."""
        current_lock = getattr(app_state, 'buttons_locked', False)
        app_state.buttons_locked = not current_lock
        stan_txt = "WŁĄCZONA" if app_state.buttons_locked else "WYŁĄCZONA"
        app_state.log(f"[Bezpieczeństwo] Blokada przycisków: {stan_txt}")

    def _handle_full_start(self, app_state):
        """Wspólna logika przycisku X / button 2 (Full Start)."""
        if not getattr(app_state, 'buttons_locked', False):
            app_state.trigger_full_start = True
        else:
            app_state.log("!! ODRZUCONO: Przyciski zablokowane. Wciśnij prawą gałkę (R3), aby odblokować.")

    def update(self, app_state):
        """Oblicza sterowanie i aktualizuje AppState"""
        try:
            events = pygame.event.get()
        except (KeyError, SystemError, Exception) as e:
            # Złap błędy SystemError wynikające z odłączenia / błędu Pygame
            events = []
            pygame.event.clear()  # Wyczyść kolejkę, żeby program nie utknął

        for event in events:
            # ==========================================
            # 0. HOTPLUG: pad/drążek podłączony / odłączony
            # ==========================================
            if event.type in (pygame.CONTROLLERDEVICEADDED, pygame.CONTROLLERDEVICEREMOVED,
                              pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self.scan_devices()
                continue

            # ==========================================
            # 1. NAJWAŻNIEJSZE: USTAWIENIE PRĘDKOŚCI (D-PAD / KRZYŻAK)
            # ==========================================

            # --- Gamepad: D-Pad jako przyciski ---
            if event.type == pygame.CONTROLLERBUTTONDOWN:

                if event.button == pygame.CONTROLLER_BUTTON_DPAD_UP:
                    self.pad_max_limit = min(config.ABSOLUTE_MAX_LIMIT, self.pad_max_limit + 1.0)
                elif event.button == pygame.CONTROLLER_BUTTON_DPAD_DOWN:
                    self.pad_max_limit = max(1.0, self.pad_max_limit - 1.0)

                # ==========================================
                # 2. PRZYCISKI GAMEPADA
                # ==========================================

                # --- PRZYCISK 'A': Tryb Obrotu ---
                elif event.button == pygame.CONTROLLER_BUTTON_A:
                    self._handle_mode_toggle(app_state)

                # --- PRZYCISK 'R3' (prawa gałka): Blokada bezpieczeństwa ---
                elif event.button == pygame.CONTROLLER_BUTTON_RIGHTSTICK:
                    self._handle_lock_toggle(app_state)

                # --- PRZYCISK 'X': Full Start (Auto) ---
                elif event.button == pygame.CONTROLLER_BUTTON_X:
                    self._handle_full_start(app_state)

            # --- Drążek Logitech: krzyżak/hat jako JOYHATMOTION ---
            elif event.type == pygame.JOYHATMOTION:
                if event.value[1] == 1:  # Strzałka w górę
                    self.pad_max_limit = min(config.ABSOLUTE_MAX_LIMIT, self.pad_max_limit + 1.0)
                elif event.value[1] == -1:  # Strzałka w dół
                    self.pad_max_limit = max(1.0, self.pad_max_limit - 1.0)

            # --- Drążek Logitech: przyciski jako JOYBUTTONDOWN ---
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    self._handle_mode_toggle(app_state)
                elif event.button == 9:
                    self._handle_lock_toggle(app_state)
                elif event.button == 2:
                    self._handle_full_start(app_state)

        joy_throttle = 0.0
        steering = 0.0
        sidle = 0.0
        analog_active = False

        # --- Drążek Logitech (flight stick) - surowe osie, jak dotychczas ---
        if self.flight_stick:
            try:
                joy = self.flight_stick
                analog_active = True

                app_state.current_speed_limit = self.pad_max_limit

                # Logitech: axis 0 - steering, axis 1 - throttle, axis 2 - sidle
                axis0 = joy.get_axis(0)
                axis1 = joy.get_axis(1)
                axis2 = joy.get_axis(2)

                steering = axis0 if abs(axis0) > config.JOYSTICK_DEADZONE else 0.0
                joy_throttle = -axis1 if abs(axis1) > config.JOYSTICK_DEADZONE else 0.0
                sidle = -axis2 if abs(axis2) > config.JOYSTICK_DEADZONE else 0.0

                # --- Awaryjne hamowanie L2 + R2, jeśli drążek je udostępnia ---
                # l2_pressed = False
                # r2_pressed = False
                # if joy.get_numaxes() > 5:
                #     if joy.get_axis(2) > 0.5: l2_pressed = True
                #     if joy.get_axis(5) > 0.5: r2_pressed = True
                # if joy.get_numbuttons() > 7:
                #     if joy.get_button(2): l2_pressed = True
                #     if joy.get_button(5): r2_pressed = True

                # if l2_pressed and r2_pressed:
                #     if not app_state.ebrake_active:
                #         app_state.ebrake_active = True
                #         app_state.ebrake_end_time = time.time() + 1.0
                #         app_state.trigger_ebrake_cmd = True
                #         app_state.log("!!! HAMOWANIE AWARYJNE (L2+R2) !!!")

            except Exception as e:
                print(f"INPUT CRASHED WITH ERROR (flight stick): {e}", flush=True)

        # --- Gamepad (SDL GameController) - znormalizowane osie ---
        elif self.gamepads:
            try:
                gp = self.gamepads[0]
                analog_active = True

                # Przekazujemy limit z D-Pada do stanu aplikacji
                app_state.current_speed_limit = self.pad_max_limit

                # Dzięki standardowemu mapowaniu SDL GameController wszystkie pady
                # (Xbox, Steam Deck, Titan itd.) używają tych samych, nazwanych
                # osi - nie trzeba już rozróżniać ich po GUID.
                axis_lx = gp.get_axis(pygame.CONTROLLER_AXIS_LEFTX)
                axis_ly = gp.get_axis(pygame.CONTROLLER_AXIS_LEFTY)
                axis_rx = gp.get_axis(pygame.CONTROLLER_AXIS_RIGHTX)
                axis_ry = gp.get_axis(pygame.CONTROLLER_AXIS_RIGHTY)

                # Sterowanie (lewa gałka - oś X)
                steering = axis_lx/32768 if abs(axis_lx/32768) > config.JOYSTICK_DEADZONE else 0.0

                # Gaz (lewa gałka - oś Y, odwrócona)
                joy_throttle = -axis_ly/32768 if abs(axis_ly/32768) > config.JOYSTICK_DEADZONE else 0.0

                # Sidle / strafe (prawa gałka) - swap_axis pozwala zamienić RX/RY,
                # analogicznie do dawnego przełącznika axis2/axis3
                sidle_raw = axis_ry if app_state.swap_axis else axis_rx
                sidle = -sidle_raw/32768 if abs(sidle_raw/32768) > config.JOYSTICK_DEADZONE else 0.0

                # --- Obsługa awaryjnego hamowania L2 + R2 ---
                trigger_l = gp.get_axis(pygame.CONTROLLER_AXIS_TRIGGERLEFT)
                trigger_r = gp.get_axis(pygame.CONTROLLER_AXIS_TRIGGERRIGHT)
                l2_pressed = trigger_l > 0.5
                r2_pressed = trigger_r > 0.5

                if l2_pressed and r2_pressed:
                    # Wyzwalaj tylko jeśli hamulec nie jest już w trakcie
                    if not app_state.ebrake_active:
                        app_state.ebrake_active = True
                        app_state.ebrake_end_time = time.time() + 1.0  # Blokada na równe 1.0s
                        app_state.trigger_ebrake_cmd = True
                        app_state.log("!!! HAMOWANIE AWARYJNE (L2+R2) !!!")

            except Exception as e:
                print(f"INPUT CRASHED WITH ERROR (gamepad): {e}", flush=True)
        else:
            app_state.current_speed_limit = self.key_max_limit

        # Wybór źródła (Drążek/Gamepad vs Klawiatura)
        if analog_active:
            app_state.target_rps = joy_throttle * app_state.current_speed_limit
            app_state.sidle_val = sidle * app_state.current_speed_limit * 0.5
            app_state.steering_val = steering * app_state.current_speed_limit * 0.25
        else:
            app_state.target_rps = self.key_throttle * app_state.current_speed_limit
            app_state.steering_val = self.key_steering * app_state.current_speed_limit * 0.25

        