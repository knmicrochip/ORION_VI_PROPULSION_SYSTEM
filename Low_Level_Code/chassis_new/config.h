// Config.h
#ifndef CONFIG_H
#define CONFIG_H
#include <Arduino.h>

// ==========================================
// WYBÓR STRONY (Zmień na SIDE_LEFT lub SIDE_RIGHT)
// ==========================================
#define SIDE_LEFT 0
#define SIDE_RIGHT 1

#define CURRENT_SIDE SIDE_LEFT  // <--- TUTAJ ZMIENIASZ STRONĘ

// --- KONFIGURACJA ZALEŻNA OD STRONY ---
#if CURRENT_SIDE == SIDE_LEFT
  #define NET_MAC_END 0x51
  #define NET_IP_END 51
  #define MQTT_CLIENT_ID "ESP32_Left_Drive"
  #define TOPIC_FEEDBACK_DEF "propulsion/feedback_left"
  #define CMD_IDX_FRONT 0
  #define CMD_IDX_REAR 1
  #define FEEDBACK_SIDE_ID 0
  #define MQTT_PUB_INTERVAL 100
#elif CURRENT_SIDE == SIDE_RIGHT
  #define NET_MAC_END 0x52
  #define NET_IP_END 52
  #define MQTT_CLIENT_ID "ESP32_Right_Drive"
  #define TOPIC_FEEDBACK_DEF "propulsion/feedback_right"
  #define CMD_IDX_FRONT 2
  #define CMD_IDX_REAR 3
  #define FEEDBACK_SIDE_ID 1
  #define MQTT_PUB_INTERVAL 100
#endif

// --- PINY (zgodne z Pins.h) ---
#define SPI_MISO_PIN  19
#define SPI_MOSI_PIN  23
#define SPI_SCK_PIN   18
#define ETH_CS_PIN    5
#define ETH_RST_PIN   27
#define CAN_TX_PIN    26
#define CAN_RX_PIN    25
#define SERVO_PIN     32

// --- KONFIGURACJA CAN ---
#define CAN_BAUDRATE  500000
#define ODRIVE_FRONT_ID 0x00
#define ODRIVE_REAR_ID  0x01

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
const int MQTT_PORT = 1883;

// --- TEMATY MQTT ---
const char* const TOPIC_SET_VEL  = "propulsion/set_velocity";
const char* const TOPIC_CMD      = "propulsion/cmd";
const char* const TOPIC_FEEDBACK = TOPIC_FEEDBACK_DEF;

// --- ZMIENNE GLOBALNE WSPÓŁDZIELONE ---
extern volatile float targetVelocity;
extern volatile float targetSteering;
extern float currentServoPos;
extern float measuredPosFront;
extern float measuredVelFront;
extern float measuredPosRear;
extern float measuredVelRear;
extern uint32_t activeErrorsFront;
extern uint32_t activeErrorsRear;

// ==========================================
// USTAWIENIA BEZPIECZEŃSTWA
// ==========================================
extern const unsigned long SAFETY_TIMEOUT;
extern unsigned long lastMqttCmdTime; 

#endif