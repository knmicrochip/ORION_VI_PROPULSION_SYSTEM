#include <Arduino.h>
#include "config.h"
#include "ODriveCAN.h"
#include "Network.h"

volatile float targetVelocity = 0.0f;
volatile float targetSteering = 0.0f;   
float currentServoPos = 1500.0;  

// Zmienne feedbackowe dla dwóch kontrolerów
float measuredPosFront = 0.0f;
float measuredVelFront = 0.0f;
float measuredPosRear = 0.0f;
float measuredVelRear = 0.0f;
uint32_t activeErrorsFront = 0;     
uint32_t activeErrorsRear = 0;     
const unsigned long SAFETY_TIMEOUT = 1000;
unsigned long lastMqttCmdTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);    
  Serial.println("\n\n>>> SYSTEM BOOT START <<<");
  initNetwork();
  initCAN();
  Serial.println(">>> SETUP COMPLETE <<<");
}

void loop() {
  unsigned long now = millis();
  
  // Watchdog braku sterowania
  if (now - lastMqttCmdTime > SAFETY_TIMEOUT) {
    if (targetVelocity != 0.0f) {
      Serial.println("!!! WATCHDOG: Utrata polaczenia - STOP !!!");
      targetVelocity = 0.0f;
    }
  }
  
  handleNetwork();
  
  // Wysyłanie do ODrive (CAN) co 50ms - zapytanie do dwóch naraz
  static unsigned long lastCanCycle = 0;
  if (now - lastCanCycle > 50) {
    lastCanCycle = now;
         
    sendVelocity(ODRIVE_FRONT_ID, targetVelocity);
    sendVelocity(ODRIVE_REAR_ID, targetVelocity);
         
    requestEncoderData(ODRIVE_FRONT_ID);
    requestEncoderData(ODRIVE_REAR_ID);
  }
  
  // Odbiór danych z CAN
  handleCANMessages();
  
  // Wysyłanie Feedbacku MQTT
  static unsigned long lastMqttPub = 0;
  if (now - lastMqttPub > MQTT_PUB_INTERVAL) { // <--- Interwał zalezny od pliku konfiguracyjnego
    lastMqttPub = now;
    sendFeedbackMessage();
  }
}