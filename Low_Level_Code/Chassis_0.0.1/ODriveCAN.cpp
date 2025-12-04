// ODriveCAN.cpp
#include "ODriveCAN.h"
#include "Network.h" // Potrzebne, żeby wysyłać błędy przez MQTT

void initCAN() {
  Serial.println("Init CAN...");
  CAN.setPins(CAN_RX_PIN, CAN_TX_PIN);
  if (!CAN.begin(CAN_BAUDRATE)) {
    Serial.println("ERROR: CAN Init Failed!");
    while(1); // Zatrzymaj, jeśli CAN nie działa
  } else {
    Serial.println("CAN Init OK");
  }
}

void sendVelocity(float velocity) {
  float torqueFF = 0.0f;
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_SET_INPUT_VEL;
  CAN.beginPacket(id);
  CAN.write((uint8_t*)&velocity, 4);
  CAN.write((uint8_t*)&torqueFF, 4);
  CAN.endPacket();
}

void setAxisState(int32_t state) {
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_SET_AXIS_STATE;
  CAN.beginPacket(id);
  CAN.write((uint8_t*)&state, 4);
  CAN.endPacket();
}

void setControlMode(int32_t controlMode, int32_t inputMode) {
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_SET_CONTROLLER_MODE;
  CAN.beginPacket(id);
  CAN.write((uint8_t*)&controlMode, 4);
  CAN.write((uint8_t*)&inputMode, 4);
  CAN.endPacket();
}

void requestEncoderData() {
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_GET_ENCODER;
  CAN.beginPacket(id, 8, true);
  CAN.endPacket();
}

void clearErrors() {
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_CLEAR_ERRORS;
  CAN.beginPacket(id);
  CAN.endPacket();
}

void rebootODrive() {
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_REBOOT_ODRIVE;
  CAN.beginPacket(id);
  CAN.endPacket();
}

void requestODriveErrors() {
  // Komenda Get_Motor_Error ma ID 0x003
  int id = (ODRIVE_NODE_ID << 5) | CMD_ID_GET_ERROR;
  
  // Wysyłamy ramkę RTR (prośbę o dane) - 3. argument 'true' oznacza RTR
  CAN.beginPacket(id, 8, true);
  CAN.endPacket();
}

void handleCANMessages() {
  int packetSize = CAN.parsePacket();
  if (packetSize) {
    long id = CAN.packetId();
    int cmdId = id & 0x01F;
    
    if (cmdId == CMD_ID_GET_ENCODER && packetSize >= 8) {
       uint8_t buffer[8];
       CAN.readBytes(buffer, 8);
       memcpy(&measuredPos, &buffer[0], 4);
       memcpy(&measuredVel, &buffer[4], 4);
       // Serial.println("[CAN] Encoder Data Recv");
    }
    else if (cmdId == CMD_ID_GET_ERROR && packetSize >= 4) {
       uint8_t buffer[4];
       CAN.readBytes(buffer, 4);
       memcpy(&activeErrors, &buffer[0], 4);
       
       Serial.print("[CAN] ODrive ERROR: "); Serial.println(activeErrors, HEX);
       sendErrorMessage(activeErrors); // Funkcja z Network.h
    }
  }
}