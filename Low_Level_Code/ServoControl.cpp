// ServoControl.cpp
#include "ServoControl.h"

// Uchwyt zadania jest lokalny, chyba że potrzebujesz go gdzie indziej
TaskHandle_t ServoTaskHandle;

void initServo() {
  Serial.print("Init LEDC on Pin "); Serial.print(SERVO_PIN); Serial.println("...");
  ledcSetup(LEDC_CHANNEL, LEDC_FREQ, LEDC_RESOLUTION);
  ledcAttachPin(SERVO_PIN, LEDC_CHANNEL);
  setServoMicroseconds(MID_PULSE);
  
  Serial.println("Creating Servo Task...");
  xTaskCreate(
    servoTask,    // Funkcja
    "ServoTask",  // Nazwa
    2048,         // Pamięć
    NULL,         // Parametry
    1,            // Priorytet
    &ServoTaskHandle // Uchwyt
  );
  Serial.println("LEDC & Task Init OK");
}

void setServoMicroseconds(int us) {
  if (us < MIN_PULSE) us = MIN_PULSE;
  if (us > MAX_PULSE) us = MAX_PULSE;
  
  long duty = ((long)us * 65536L) / 20000L;
  ledcWrite(LEDC_CHANNEL, duty);
}

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
       // setServoMicroseconds((int)currentServoPos); // Opcjonalnie usuń printy w produkcji
    } 
    else {
       if (abs(diff) > 0.5) {
          currentServoPos = targetPulse;
          // Serial.println("[TASK] Final Adjust");
       }
    }
    
    // Zawsze aktualizuj PWM
    setServoMicroseconds((int)currentServoPos);

    // Usypiamy wątek na 20ms
    vTaskDelay(20 / portTICK_PERIOD_MS); 
  }
}