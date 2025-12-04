// Config.h
#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// --- PINY ---
#define ETH_CS_PIN    21
#define ETH_RST_PIN   22
#define CAN_TX_PIN    5
#define CAN_RX_PIN    4
#define SERVO_PIN     32 

// --- KONFIGURACJA CAN ---
#define CAN_BAUDRATE  250000
#define ODRIVE_NODE_ID 0

// --- KONFIGURACJA SERWA ---
#define LEDC_CHANNEL    0
#define LEDC_FREQ       50      
#define LEDC_RESOLUTION 16      
const int MIN_PULSE = 500;   
const int MAX_PULSE = 2500;  
const int MID_PULSE = 1500;
const float SMOOTH_FACTOR = 0.08; 
const float DEADBAND = 3.0;

// --- KONFIGURACJA SIECI ---
// Adres IP i MAC są definiowane w Network.cpp, ale porty tutaj
const int MQTT_PORT = 1883;

// --- TEMATY MQTT ---
const char* const TOPIC_SET_VEL  = "odrive/set_velocity";
const char* const TOPIC_CMD      = "odrive/cmd";
const char* const TOPIC_FEEDBACK = "odrive/feedback";

// --- ZMIENNE GLOBALNE WSPÓŁDZIELONE (Deklaracje extern) ---
// To pozwala innym plikom wiedzieć, że te zmienne istnieją w głównym pliku
extern volatile float targetVelocity;
extern volatile float targetSteering;
extern float currentServoPos;
extern float measuredPos;
extern float measuredVel;
extern uint32_t activeErrors;

// ==========================================
// USTAWIENIA BEZPIECZEŃSTWA
// ==========================================
extern const unsigned long SAFETY_TIMEOUT;
extern unsigned long lastMqttCmdTime; 


#endif