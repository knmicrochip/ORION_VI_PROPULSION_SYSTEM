// Network.cpp
#include "Network.h"

// Zmieniony adres MAC (końcówka 0x51, odpowiadająca IP), aby zapobiec konfliktom z ARM_ID1
byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0x52 };
IPAddress ip(192, 168, 1, 52); 
const char* mqtt_server = "192.168.1.1"; 

EthernetClient ethClient;
PubSubClient client(ethClient);

void executeCommand(int cmd, int node_id) {
    switch(cmd) {
        case 1: setAxisState(node_id, AXIS_STATE_ENCODER_OFFSET_CALIBRATION); break;
        case 2: setAxisState(node_id, AXIS_STATE_CLOSED_LOOP_CONTROL); break;
        case 3: setControlMode(node_id, CONTROL_MODE_VELOCITY_CONTROL, INPUT_MODE_PASSTHROUGH); break;
        case 4: setControlMode(node_id, CONTROL_MODE_VELOCITY_CONTROL, INPUT_MODE_VEL_RAMP); break;
        case 5: requestODriveErrors(node_id); break;
        case 6: rebootODrive(node_id); break;
    }
}

void callback(char* topic, byte* payload, unsigned int length) {
  if (length > 512) return; 
  
  String topicStr = String(topic);
  String messageTemp;
  messageTemp.reserve(length);
  for (unsigned int i = 0; i < length; i++) messageTemp += (char)payload[i];

  if (topicStr == TOPIC_SET_VEL) {
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, messageTemp);
    lastMqttCmdTime = millis();
    if (!error) {
      if (doc.containsKey("velocity")) targetVelocity = doc["velocity"];
      if (doc.containsKey("steering")) {
        float s = doc["steering"];
        if (s < -1.0f) s = -1.0f;
        if (s > 1.0f) s = 1.0f;
        targetSteering = s;
      }
    }
  }
  else if (topicStr == TOPIC_CMD) {
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, messageTemp);
    lastMqttCmdTime = millis();
    
    if (!error && doc.is<JsonArray>()) {
        JsonArray arr = doc.as<JsonArray>();
        if(arr.size() == 5) {
            // Indeksy dla lewej strony: [0] = Lewy Przód, [1] = Lewy Tył, [4] = Wszystkie
            int lf_cmd = arr[2];
            int lr_cmd = arr[3];
            int override_cmd = arr[4];
            
            int cmd_front = override_cmd ? override_cmd : lf_cmd;
            int cmd_rear = override_cmd ? override_cmd : lr_cmd;

            if(cmd_front != 0) executeCommand(cmd_front, ODRIVE_FRONT_ID);
            if(cmd_rear != 0) executeCommand(cmd_rear, ODRIVE_REAR_ID);
        }
    }
  }
}

void reconnect() {
  if (!client.connected()) {
      static unsigned long lastRec = 0;
      if (millis() - lastRec > 5000) {
        lastRec = millis();
        Serial.print("[MQTT] Connecting to "); Serial.print(mqtt_server); Serial.println("...");
        if (client.connect("ESP32_Right_Drive")) {  // Unikalna nazwa klienta!
          Serial.println("[MQTT] Connected!");
          client.subscribe(TOPIC_SET_VEL);
          client.subscribe(TOPIC_CMD);
        }
      }
  }
}

void initNetwork() {
  Serial.println("Init Ethernet...");
  
  // Bezpieczniejszy restart jak w ARM_ID1
  pinMode(ETH_RST_PIN, OUTPUT);
  digitalWrite(ETH_RST_PIN, LOW); delay(100);
  digitalWrite(ETH_RST_PIN, HIGH); delay(200); 
  
  SPI.begin(SPI_SCK_PIN, SPI_MISO_PIN, SPI_MOSI_PIN, ETH_CS_PIN);
  Ethernet.init(ETH_CS_PIN);
  Ethernet.begin(mac, ip);
  
  client.setServer(mqtt_server, MQTT_PORT);
  client.setCallback(callback);
  client.setBufferSize(1024); // Zwiększony bufor, zapobiega ucinaniu wiadomości w pętli
}

void handleNetwork() {
  reconnect();
  client.loop();
}

void sendFeedbackMessage() {
    if (!client.connected()) return;

    // Tworzenie ramki bezpiecznie z użyciem biblioteki, tak jak zrobione w ARM_ID1.
    // Format docelowy: [side, v_front, p_front, v_rear, p_rear]
    StaticJsonDocument<256> doc;
    doc.add(1); // 0 oznacza lewą stronę, zgodnie z logiką Pythonowego GUI
    doc.add(measuredVelFront);
    doc.add(measuredPosFront);
    doc.add(measuredVelRear);
    doc.add(measuredPosRear);

    char buffer[256];
    serializeJson(doc, buffer);
    client.publish(TOPIC_FEEDBACK, buffer);
}

void sendErrorMessage(uint32_t errorDesc, int odrive_id) {
    if (!client.connected()) return;

    StaticJsonDocument<256> doc;
    doc["error"] = errorDesc;
    doc["odrive_id"] = odrive_id;
    
    char errBuf[256];
    serializeJson(doc, errBuf);
    client.publish(TOPIC_FEEDBACK, errBuf);
}