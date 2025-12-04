// Network.h
#ifndef NETWORK_H
#define NETWORK_H

#include <Arduino.h>
#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "Config.h"
#include "ODriveCAN.h" // Potrzebne dla clearErrors()

void initNetwork();
void handleNetwork(); // Wywoływane w loop()
void sendFeedbackMessage(float vel, float pos);
void sendErrorMessage(uint32_t errorDesc);

#endif