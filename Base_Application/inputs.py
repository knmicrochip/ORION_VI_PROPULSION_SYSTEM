# inputs.py
import pygame
from config import *

class InputManager:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.joysticks = []
        self.reset_joysticks()
        
        # Stan klawiatury
        self.key_throttle = 0.0
        self.key_max_limit = 10.0
        self.current_speed_limit = 10.0

    def reset_joysticks(self):
        pygame.joystick.quit()
        pygame.joystick.init()
        count = pygame.joystick.get_count()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(count)]
        for joy in self.joysticks:
            joy.init()
        return self.joysticks

    def handle_keyboard(self, event_type, keysym):
        k = keysym.lower()
        if event_type == 'press':
            if k == 'w': self.key_throttle = 1.0
            elif k == 's': self.key_throttle = -1.0
            elif k == 'r': self.key_max_limit = min(ABSOLUTE_MAX_LIMIT, self.key_max_limit + 1.0)
            elif k == 'f': self.key_max_limit = max(1.0, self.key_max_limit - 1.0)
        elif event_type == 'release':
            if k in ['w', 's']: self.key_throttle = 0.0
            
    def get_control_values(self):
        pygame.event.pump()
        
        # 1. Prędkość
        target_vel = 0.0
        joy_active = False
        
        if self.joysticks:
            try:
                joy = self.joysticks[0]
                # Limit prędkości z slidera (axis 3)
                if joy.get_numaxes() > 3:
                    axis3 = joy.get_axis(3)
                    self.current_speed_limit = ((1.0 - axis3) / 2.0) * ABSOLUTE_MAX_LIMIT
                else:
                    self.current_speed_limit = self.key_max_limit
                
                # Gaz (axis 1)
                axis1 = -joy.get_axis(1)
                if abs(axis1) > JOYSTICK_DEADZONE:
                    target_vel = axis1 * self.current_speed_limit
                    joy_active = True
            except: pass
        else:
            self.current_speed_limit = self.key_max_limit

        if not joy_active:
            target_vel = self.key_throttle * self.current_speed_limit
            
        # 2. Skręt
        steering_val = 0.0
        if self.joysticks:
            try:
                joy = self.joysticks[0]
                if joy.get_numaxes() > STEERING_AXIS_INDEX:
                    steering_val = joy.get_axis(STEERING_AXIS_INDEX)
                elif joy.get_numaxes() > 2:
                    steering_val = joy.get_axis(2) # Fallback
            except: pass
            
        return target_vel, steering_val, self.current_speed_limit