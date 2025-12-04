/*
 * FINAL DEBUG CODE: ESP32 + MQTT + ODrive + LEDC SERVO (FreeRTOS Version)
 * Wersja Modułowa
 */

#include <Arduino.h>

// Dołączamy nasze moduły
#include "Config.h"
#include "ServoControl.h"
#include "ODriveCAN.h"
#include "Network.h"

// ==========================================
// DEFINICJA ZMIENNYCH GLOBALNYCH
// (W Config.h były tylko deklaracje 'extern')
// ==========================================
volatile float targetVelocity = 0.0f;
volatile float targetSteering = 0.0f;  
float currentServoPos = 1500.0; 

// Zmienne feedbackowe
float measuredPos = 0.0f;
float measuredVel = 0.0f;
uint32_t activeErrors = 0;    

// ==========================================
// USTAWIENIA BEZPIECZEŃSTWA
// ==========================================
const unsigned long SAFETY_TIMEOUT = 1000;
unsigned long lastMqttCmdTime = 0;
// ==========================================
// SETUP
// ==========================================
void setup() {
  
  Serial.begin(115200);
  delay(1000); 
  Serial.println("\n\n>>> SYSTEM BOOT START <<<");

  // Inicjalizacja modułów
  initServo();
  initNetwork();
  initCAN();

  Serial.println(">>> SETUP COMPLETE <<<");
}

// ==========================================
// LOOP
// ==========================================
void loop() {
  unsigned long now = millis();
  
  if (now - lastMqttCmdTime > SAFETY_TIMEOUT) {
    if (targetVelocity != 0.0f) {
      Serial.println("!!! WATCHDOG: Utrata polaczenia - STOP !!!");
      targetVelocity = 0.0f;
    }
  }

  // 1. Obsługa MQTT i Ethernet
  handleNetwork();

  // 2. Wysyłanie do ODrive (CAN) co 50ms
  static unsigned long lastCanCycle = 0;
  if (now - lastCanCycle > 50) {
    lastCanCycle = now;
    // Serial.println("[CAN] Sending Vel...");
    sendVelocity(targetVelocity);
    requestEncoderData();
  }

  // 3. Odbiór danych z CAN
  handleCANMessages();

  // 4. Wysyłanie Feedbacku MQTT co 100ms
  static unsigned long lastMqttPub = 0;
  if (now - lastMqttPub > 100) {
    lastMqttPub = now;
    sendFeedbackMessage(measuredVel, measuredPos);
  }
}