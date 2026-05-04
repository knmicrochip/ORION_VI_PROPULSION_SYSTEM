#include <Arduino.h>
#include "config.h"
#include "ODriveCAN.h"
#include "Network.h"

volatile float targetVelocityFront = 0.0f;
volatile float targetVelocityRear = 0.0f;
volatile float targetSteeringFront = 0.0f;
volatile float targetSteeringRear = 0.0f;   

float currentServoPosA = MID_PULSE;  
float currentServoPosB = MID_PULSE;  

float servoVoltageA = 0.0f;
float servoVoltageB = 0.0f;
float servoCurrentA = 0.0f;
float servoCurrentB = 0.0f;

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
  
  // Konfiguracja pinów wejściowych dla pomiarów
  pinMode(SV_VFB_A, INPUT);
  pinMode(SV_VFB_B, INPUT);
  pinMode(SV_CFB_A, INPUT);
  pinMode(SV_CFB_B, INPUT);

  // Inicjalizacja PWM dla serw A i B
  ledcSetup(LEDC_CHANNEL_A, LEDC_FREQ, LEDC_RESOLUTION);
  ledcAttachPin(SV_A_PIN, LEDC_CHANNEL_A);
  
  ledcSetup(LEDC_CHANNEL_B, LEDC_FREQ, LEDC_RESOLUTION);
  ledcAttachPin(SV_B_PIN, LEDC_CHANNEL_B);
  
  uint32_t dutyMid = (uint32_t)((MID_PULSE * 65536.0f) / 20000.0f);
  ledcWrite(LEDC_CHANNEL_A, dutyMid);
  ledcWrite(LEDC_CHANNEL_B, dutyMid);

  initNetwork();
  initCAN();
  Serial.println(">>> SETUP COMPLETE <<<");
}

void updateServo(float targetRad, float &currentPos, uint8_t channel) {
  float normalized = constrain(targetRad / MAX_STEER_RAD, -1.0f, 1.0f);
  float targetPulse = MID_PULSE + (normalized * (MAX_PULSE - MID_PULSE));
  
  if (abs(targetPulse - currentPos) > DEADBAND) {
    currentPos += (targetPulse - currentPos) * SMOOTH_FACTOR;
  }
  
  uint32_t duty = (uint32_t)((currentPos * 65536.0f) / 20000.0f);
  ledcWrite(channel, duty);
}

void readSensors() {
  // Przeliczanie odczytów napięcia (Zakładamy prosty odczyt 0-3.3V)
  servoVoltageA = (analogRead(SV_VFB_A) * ADC_VREF) / ADC_RES;
  servoVoltageB = (analogRead(SV_VFB_B) * ADC_VREF) / ADC_RES;

  // Przeliczanie prądu z ACS712
  float rawVoltageCFB_A = (analogRead(SV_CFB_A) * ADC_VREF) / ADC_RES;
  float rawVoltageCFB_B = (analogRead(SV_CFB_B) * ADC_VREF) / ADC_RES;
  
  servoCurrentA = (rawVoltageCFB_A - ACS712_OFFSET) / ACS712_SENS;
  servoCurrentB = (rawVoltageCFB_B - ACS712_OFFSET) / ACS712_SENS;
}

void loop() {
  unsigned long now = millis();
  
  if (now - lastMqttCmdTime > SAFETY_TIMEOUT) {
    if (targetVelocityFront != 0.0f || targetVelocityRear != 0.0f) {
      Serial.println("!!! WATCHDOG: Utrata polaczenia - STOP !!!");
      targetVelocityFront = 0.0f;
      targetVelocityRear = 0.0f;
      targetSteeringFront = 0.0f;
      targetSteeringRear = 0.0f;
    }
  }
  
  handleNetwork();

  // Sterowanie niezależne serwem Przód(A) i Tył(B)
  updateServo(targetSteeringFront, currentServoPosA, LEDC_CHANNEL_A);
  updateServo(targetSteeringRear, currentServoPosB, LEDC_CHANNEL_B);
  
  // Odczyt z czujników
  readSensors();

  static unsigned long lastCanCycle = 0;
  if (now - lastCanCycle > 50) {
    lastCanCycle = now;
    sendVelocity(ODRIVE_FRONT_ID, targetVelocityFront * DIR_FRONT);
    sendVelocity(ODRIVE_REAR_ID, targetVelocityRear * DIR_REAR);
    requestEncoderData(ODRIVE_FRONT_ID);
    requestEncoderData(ODRIVE_REAR_ID);
  }
  
  handleCANMessages();
  
  static unsigned long lastMqttPub = 0;
  if (now - lastMqttPub > MQTT_PUB_INTERVAL) { 
    lastMqttPub = now;
    sendFeedbackMessage();
  }
}