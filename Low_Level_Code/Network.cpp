// Network.cpp
#include "Network.h"

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };
IPAddress ip(192, 168, 1, 177);      
const char* mqtt_server = "192.168.1.1"; 

EthernetClient ethClient;
PubSubClient client(ethClient);

void callback(char* topic, byte* payload, unsigned int length) {
  // Serial.print("[MQTT] Recv Topic: "); Serial.println(topic);
  
  if (length > 512) {
    Serial.println("[MQTT] ERROR: Payload too big!");
    return; 
  }
  String topicStr = String(topic);
  String messageTemp;
  messageTemp.reserve(length);
  for (int i = 0; i < length; i++) messageTemp += (char)payload[i];

  if (topicStr == TOPIC_SET_VEL) {
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, messageTemp);
    lastMqttCmdTime = millis();
    if (!error) {
      if (doc.containsKey("velocity")) {
        targetVelocity = doc["velocity"];
        Serial.println(targetVelocity);
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
  else if (topicStr == TOPIC_CMD) {
    lastMqttCmdTime = millis();
    Serial.print("Komenda MQTT: ");
    Serial.println(messageTemp);

    if (messageTemp == "calibrate") {
      setAxisState(AXIS_STATE_ENCODER_OFFSET_CALIBRATION);
    }
    else if (messageTemp == "closed_loop") {
      setAxisState(AXIS_STATE_CLOSED_LOOP_CONTROL);
    }
    else if (messageTemp == "set_vel_mode") {
      setControlMode(CONTROL_MODE_VELOCITY_CONTROL, INPUT_MODE_PASSTHROUGH);
      Serial.println(">> Tryb: VELOCITY PASSTHROUGH");
    }
    else if (messageTemp == "set_ramp_mode") {
      setControlMode(CONTROL_MODE_VELOCITY_CONTROL, INPUT_MODE_VEL_RAMP);
      Serial.println(">> Tryb: VELOCITY RAMP");
    }
    else if (messageTemp == "reboot_odrive") { // <--- Obsługa Reboot
      rebootODrive();
      Serial.println(">> REBOOTING ODRIVE...");
    }
  }
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
          Serial.print("[MQTT] Failed, rc="); Serial.println(client.state());
        }
      }
  }
}

void initNetwork() {
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
  
  client.setServer(mqtt_server, MQTT_PORT);
  client.setCallback(callback);
  client.setBufferSize(512);
}

void handleNetwork() {
  reconnect();
  client.loop();
}

void sendFeedbackMessage(float vel, float pos) {
    if (client.connected()) {
       char msg[128];
       snprintf(msg, sizeof(msg), "{\"v_meas\":%.2f,\"p_meas\":%.2f}", vel, pos);
       client.publish(TOPIC_FEEDBACK, msg);
    }
}

void sendErrorMessage(uint32_t errorDesc) {
    if (client.connected()) {
       char errBuf[64];
       snprintf(errBuf, sizeof(errBuf), "{\"error\": \"0x%X\"}", errorDesc);
       client.publish(TOPIC_FEEDBACK, errBuf);
    }
}