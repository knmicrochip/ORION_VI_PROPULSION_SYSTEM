/*
 * FINAL DEBUG CODE: ESP32 + MQTT + ODrive + LEDC SERVO (FreeRTOS Version)
 * Wersja z pełnym logowaniem na Serial (Debug)
 */

#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <CAN.h>
#include <ArduinoJson.h>

// BLOKADA RESETÓW NAPIĘCIOWYCH
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// ==========================================
// 1. PINY I KONFIGURACJA
// ==========================================
#define ETH_CS_PIN    21
#define ETH_RST_PIN   22
#define CAN_TX_PIN    5
#define CAN_RX_PIN    4
// UWAGA: Użytkownik zmienił pin na 32 w poprzednim kroku
#define SERVO_PIN     32 

#define CAN_BAUDRATE  250000

// --- SERWO (LEDC HARDWARE) ---
#define LEDC_CHANNEL    0
#define LEDC_FREQ       50      
#define LEDC_RESOLUTION 16      

const int MIN_PULSE = 500;   
const int MAX_PULSE = 2500;  
const int MID_PULSE = 1500;  

// FIZYKA RUCHU
const float SMOOTH_FACTOR = 0.08; 
const float DEADBAND = 3.0;       

// --- SIECI ---
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 1, 177);      
const char* mqtt_server = "192.168.1.1"; 
const int mqtt_port = 1883;

const char* TOPIC_SET_VEL  = "odrive/set_velocity";
const char* TOPIC_CMD      = "odrive/cmd";
const char* TOPIC_FEEDBACK = "odrive/feedback";

// --- ODRIVE ---
#define ODRIVE_NODE_ID 0
#define CMD_ID_GET_ERROR       0x003
#define CMD_ID_SET_AXIS_STATE  0x007
#define CMD_ID_GET_ENCODER     0x009
#define CMD_ID_SET_INPUT_VEL   0x00D
#define CMD_ID_CLEAR_ERRORS    0x018

EthernetClient ethClient;
PubSubClient client(ethClient);

// Zmienne współdzielone 
volatile float targetVelocity = 0.0f;
volatile float targetSteering = 0.0f;  
float currentServoPos = 1500.0; 

// Zmienne feedbackowe
float measuredPos = 0.0f;
float measuredVel = 0.0f;
uint32_t activeErrors = 0;    

// Uchwyt zadania serwa
TaskHandle_t ServoTaskHandle;

// Deklaracje
void sendVelocity(float velocity);
void requestEncoderData();
void clearErrors();
void setServoMicroseconds(int us);

// ==========================================
// STEROWANIE PWM (Logowanie)
// ==========================================
void setServoMicroseconds(int us) {
  // DEBUG PRINT
  // Serial.print("[PWM] Set US: "); Serial.println(us); // Odkomentuj jeśli chcesz bardzo dużo spamu

  if (us < MIN_PULSE) us = MIN_PULSE;
  if (us > MAX_PULSE) us = MAX_PULSE;
  
  long duty = ((long)us * 65536L) / 20000L;
  
  // Krytyczny moment - tutaj często następuje reset
  ledcWrite(LEDC_CHANNEL, duty);
}

// ==========================================
// OSOBNE ZADANIE DLA SERWA
// ==========================================
void servoTask(void * parameter) {
  Serial.println("[TASK] Servo Task STARTED");
  
  for(;;) {
    // 1. Oblicz cel
    float targetPulse = 1500.0 + (targetSteering * 1000.0);
    
    if (targetPulse < (float)MIN_PULSE) targetPulse = (float)MIN_PULSE;
    if (targetPulse > (float)MAX_PULSE) targetPulse = (float)MAX_PULSE;

    // 2. Wygładzanie
    float diff = targetPulse - currentServoPos;

    if (abs(diff) > DEADBAND) {
       currentServoPos += (diff * SMOOTH_FACTOR);
       
       // Logujemy tylko gdy faktycznie zmieniamy pozycję
       Serial.print("[TASK] Moving to: "); Serial.println((int)currentServoPos);
       
       setServoMicroseconds((int)currentServoPos);
    } 
    else {
       // Dociąganie do celu
       if (abs(diff) > 0.5) {
          currentServoPos = targetPulse;
          Serial.println("[TASK] Final Adjust");
          setServoMicroseconds((int)currentServoPos);
       }
    }

    // Usypiamy wątek na 20ms
    vTaskDelay(20 / portTICK_PERIOD_MS); 
  }
}

// ==========================================
// MQTT CALLBACK
// ==========================================
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("[MQTT] Recv Topic: "); Serial.println(topic);
  
  if (length > 512) {
    Serial.println("[MQTT] ERROR: Payload too big!");
    return; 
  }

  String messageTemp;
  messageTemp.reserve(length);
  for (int i = 0; i < length; i++) messageTemp += (char)payload[i];

  // Serial.print("[MQTT] Payload: "); Serial.println(messageTemp);

  if (String(topic) == TOPIC_SET_VEL) {
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, messageTemp);

    if (!error) {
      if (doc.containsKey("velocity")) {
        targetVelocity = doc["velocity"];
        // Serial.print("Set Vel: "); Serial.println(targetVelocity);
      }
      if (doc.containsKey("steering")) {
        float s = doc["steering"];
        if (s < -1.0f) s = -1.0f;
        if (s > 1.0f) s = 1.0f;
        
        targetSteering = s;
        Serial.print("[MQTT] New Steering Target: "); Serial.println(targetSteering);
      }
    } else {
      Serial.print("[MQTT] JSON Error: "); Serial.println(error.c_str());
    }
  }
  else if (String(topic) == TOPIC_CMD) {
     Serial.print("[MQTT] CMD: "); Serial.println(messageTemp);
     if (messageTemp == "clear_errors") clearErrors();
  }
}

// ==========================================
// SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  // Czekamy chwilę na otwarcie monitora
  delay(1000); 
  Serial.println("\n\n>>> SYSTEM BOOT START <<<");

  // 1. Start PWM
  Serial.print("Init LEDC on Pin "); Serial.print(SERVO_PIN); Serial.println("...");
  ledcSetup(LEDC_CHANNEL, LEDC_FREQ, LEDC_RESOLUTION);
  ledcAttachPin(SERVO_PIN, LEDC_CHANNEL);
  setServoMicroseconds(MID_PULSE);
  Serial.println("LEDC Init OK");

  // 2. Start Ethernet
  Serial.println("Init Ethernet...");
  pinMode(ETH_RST_PIN, OUTPUT);
  digitalWrite(ETH_RST_PIN, LOW); delay(100);
  digitalWrite(ETH_RST_PIN, HIGH); delay(100);
  
  Ethernet.init(ETH_CS_PIN);
  Ethernet.begin(mac, ip);
  
  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    Serial.println("ERROR: W5500 not found!");
  } else {
    Serial.print("Ethernet IP: "); Serial.println(Ethernet.localIP());
  }
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  client.setBufferSize(512);

  // 3. Start CAN
  Serial.println("Init CAN...");
  CAN.setPins(CAN_RX_PIN, CAN_TX_PIN);
  if (!CAN.begin(CAN_BAUDRATE)) {
    Serial.println("ERROR: CAN Init Failed!");
  } else {
    Serial.println("CAN Init OK");
  }

  // 4. Start Task
  Serial.println("Creating Servo Task...");
  xTaskCreate(
    servoTask,    // Funkcja
    "ServoTask",  // Nazwa
    2048,         // Pamięć
    NULL,         // Parametry
    1,            // Priorytet
    &ServoTaskHandle // Uchwyt
  );
  
  Serial.println(">>> SETUP COMPLETE <<<");
}

void reconnect() {
  
  if (!client.connected()) {
     static unsigned long lastRec = 0;
     if (millis() - lastRec > 5000) {
        lastRec = millis();
        Serial.print("[MQTT] Connecting to "); Serial.print(mqtt_server); Serial.println("...");
        if (client.connect("ESP32_ODrive")) {
          Serial.println("[MQTT] Connected!");
          client.subscribe(TOPIC_SET_VEL);
          client.subscribe(TOPIC_CMD);
        } else {
            digitalWrite(ETH_RST_PIN, LOW); delay(100);
            digitalWrite(ETH_RST_PIN, HIGH); delay(100);
          Serial.print("[MQTT] Failed, rc="); Serial.println(client.state());
        }
     }
  }
}

// ==========================================
// LOOP
// ==========================================
void loop() {
  reconnect();
  client.loop();

  unsigned long now = millis();

  // CAN co 50ms
  static unsigned long lastCanCycle = 0;
  if (now - lastCanCycle > 50) {
    lastCanCycle = now;
    Serial.println("[CAN] Sending Vel...");
    sendVelocity(targetVelocity);
    requestEncoderData();
  }

  // Odbiór CAN
  int packetSize = CAN.parsePacket();
  if (packetSize) {
    long id = CAN.packetId();
    int cmdId = id & 0x01F;
    
    if (cmdId == CMD_ID_GET_ENCODER && packetSize >= 8) {
       uint8_t buffer[8];
       CAN.readBytes(buffer, 8);
       memcpy(&measuredPos, &buffer[0], 4);
       memcpy(&measuredVel, &buffer[4], 4);
       Serial.println("[CAN] Encoder Data Recv");
    }
    else if (cmdId == CMD_ID_GET_ERROR && packetSize >= 4) {
       uint8_t buffer[4];
       CAN.readBytes(buffer, 4);
       memcpy(&activeErrors, &buffer[0], 4);
       
       Serial.print("[CAN] ODrive ERROR: "); Serial.println(activeErrors, HEX);
       
       char errBuf[64];
       snprintf(errBuf, sizeof(errBuf), "{\"error\": \"0x%X\"}", activeErrors);
       client.publish(TOPIC_FEEDBACK, errBuf);
    }
  }

  // MQTT Feedback co 100ms
  static unsigned long lastMqttPub = 0;
  if (now - lastMqttPub > 100) {
    lastMqttPub = now;
    if (client.connected()) {
       char msg[128];
       snprintf(msg, sizeof(msg), "{\"v_meas\":%.2f,\"p_meas\":%.2f}", measuredVel, measuredPos);
       client.publish(TOPIC_FEEDBACK, msg);
       Serial.println("[MQTT] Feedback Sent");
    }
  }
}

// ==========================================
// FUNKCJE POMOCNICZE
// ==========================================
void sendVelocity(float velocity) {
  float torqueFF = 0.0f;
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_SET_INPUT_VEL;
  CAN.beginPacket(id);
  CAN.write((uint8_t*)&velocity, 4);
  CAN.write((uint8_t*)&torqueFF, 4);
  CAN.endPacket();
}
void requestEncoderData() {
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_GET_ENCODER;
  CAN.beginPacket(id, 8, true);
  CAN.endPacket();
}
void clearErrors() {
  Serial.println("[CMD] Clearing ODrive Errors...");
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_CLEAR_ERRORS;
  CAN.beginPacket(id);
  CAN.endPacket();
}
