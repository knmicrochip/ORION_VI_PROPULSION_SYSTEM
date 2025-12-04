// ServoControl.h
#ifndef SERVO_CONTROL_H
#define SERVO_CONTROL_H

#include <Arduino.h>
#include "Config.h"

void initServo();
void setServoMicroseconds(int us);
void servoTask(void * parameter); // Zadanie FreeRTOS

#endif