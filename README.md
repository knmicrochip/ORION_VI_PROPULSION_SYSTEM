## 📑 Spis Treści
1. [Przegląd Systemu (Executive Summary)](#1-przegląd-systemu-executive-summary)
2. [Architektura Systemu i Przepływ Danych](#2-architektura-systemu-i-przepływ-danych)
3. [Topologia Sieciowa i Konfiguracja IP](#3-topologia-sieciowa-i-konfiguracja-ip)
4. [Protokół Komunikacyjny (MQTT & CAN)](#4-protokół-komunikacyjny-mqtt--can)
5. [Konfiguracja Sprzętowa i Mapa Pinów (ESP32)](#5-konfiguracja-sprzętowa-i-mapa-pinów-esp32)
6. [Algorytmy Sterowania i Bezpieczeństwo](#6-algorytmy-sterowania-i-bezpieczeństwo)
7. [Struktura Repozytorium](#7-struktura-repozytorium)
8. [Instrukcja Wdrożenia (Deployment)](#8-instrukcja-wdrożenia-deployment)

---

## 1. Przegląd Systemu (Executive Summary)

**ORION VI Propulsion System** to zaawansowana, rozproszona architektura oprogramowania przeznaczona do sterowania układem napędowym oraz kierowniczym pojazdu/łazika. System integruje stację bazową z interfejsem graficznym (aplikacja Python) z niskopoziomowym oprogramowaniem układowym (C++/Arduino dla ESP32). 

Zastosowanie komunikacji Ethernet (układ W5500), protokołu MQTT oraz magistrali CAN zapewnia wysoką niezawodność, niskie opóźnienia i odporność na zakłócenia, co jest krytyczne w systemach sterowania ruchem. Moduł mikrokontrolera odbiera komendy od operatora, przelicza je przy użyciu regulatorów PID na fizyczne kąty wychylenia serwomechanizmów oraz wysyła wartości zadane prędkości do sterowników silników ODrive.

---

## 2. Architektura Systemu i Przepływ Danych

System działa w paradygmacie asynchronicznej pętli sprzężenia zwrotnego:

1. **Aplikacja PC (Control Station):** Odczytuje stan kontrolerów (gamepadów) przy użyciu biblioteki `pygame` (w tym uwzględniając martwe strefy na poziomie `0.2`). Generuje ramki JSON i publikuje je na Brokerze MQTT. Wątek GUI odświeża się z częstotliwością ~20 Hz (co 50 ms).
2. **Broker MQTT:** (Adres IP: `192.168.1.1:1883`) - pełni rolę głównego węzła wymiany wiadomości.
3. **Firmware ESP32:** Subskrybuje główny temat sterujący (`propulsion/cmd`). Moduł odbiera JSON, parsuje go, a następnie:
   - Wysyła docelową prędkość (RPS - Rotations Per Second) do kontrolerów ODrive (Front/Rear) używając magistrali **CAN 2.0B** o prędkości 500 kbps.
   - Płynnie wysterowuje serwomechanizmy odpowiadające za skręt, korzystając z programowego algorytmu PID w celu ochrony mechaniki.
4. **Pętla zwrotna (Feedback):** ESP32 czyta dane z enkoderów ODrive (po CAN) oraz przetworników ADC (napięcie/prąd serw) i wysyła pakiet zwrotny na dedykowane tematy MQTT (np. `propulsion/feedback_left`).

---

## 3. Topologia Sieciowa i Konfiguracja IP

Sieć opiera się na statycznej i powtarzalnej konfiguracji IP wewnątrz podsieci `192.168.1.x`. System sprzętowy łazika jest podzielony na Stronę Lewą i Prawą (konfigurowalne makrami `#define CURRENT_SIDE` w pliku `config.h`).

### Broker MQTT / Stacja Bazowa:
* **Adres Brokera IP:** `192.168.1.1`
* **Port MQTT:** `1883`

### Urządzenia Pokładowe (ESP32):
| Konfiguracja | Moduł Lewy (SIDE_LEFT) | Moduł Prawy (SIDE_RIGHT) |
| :--- | :--- | :--- |
| **MAC Address** | `DE:AD:BE:EF:FE:51` | `DE:AD:BE:EF:FE:52` |
| **IP Address** | `192.168.1.51` | `192.168.1.52` |
| **MQTT Client ID** | `ESP32_Left_Drive` | `ESP32_Right_Drive` |
| **Feedback Topic**| `propulsion/feedback_left` | `propulsion/feedback_right` |
| **Target ODrive CAN ID**| `0x00` (Front), `0x01` (Rear)| `0x00` (Front), `0x01` (Rear) |

---

## 4. Protokół Komunikacyjny (MQTT & CAN)

### 4.1. Komendy Sterujące MQTT (TX - Stacja Bazowa do Łazika)
Wszystkie dane wysyłane są w strukturze JSON na wspólny temat **`propulsion/cmd`**. Wersja API przesyła złożony słownik:

```
```text?code_stdout&code_event_index=2
File generated successfully.

```json
{
  "eventType": "propulsion",
  "velocity": {
    "fl_speed": 12.5, "rl_speed": 12.5,
    "fr_speed": 12.5, "rr_speed": 12.5,
    "fl_rad": 0.5, "rl_rad": 0.5,
    "fr_rad": 0.5, "rr_rad": 0.5
  }
}
```

### 4.2. Telemetria MQTT (RX - Łazik do Stacji Bazowej)
ESP32 publikuje telemetrię co 100 ms (interwał `MQTT_PUB_INTERVAL`):

```json
{
  "side_id": 0,
  "vel_front": 5.2, "pos_front": 104.3,
  "vel_rear": 5.2, "pos_rear": 103.8,
  "servoA_vfb": 6.0, "servoA_cfb": 1.2,
  "servoB_vfb": 6.0, "servoB_cfb": 1.1
}
```

### 4.3. Magistrala CAN (Komunikacja z ODrive)
Aplikacja wysyła proste polecenia (ID zależne od `node_id << 5` OR `cmd_id`):
* `CMD_ID_SET_INPUT_VEL (0x00D)`
* `CMD_ID_SET_AXIS_STATE (0x007)`
* Odbiór: `CMD_ID_GET_ENCODER (0x009)` - zawiera aktualną pozycję (4 bajty float) i prędkość (4 bajty float).

---

## 5. Konfiguracja Sprzętowa i Mapa Pinów (ESP32)

Wszystkie peryferia zostały sztywno zamapowane w `config.h`. 

| Komponent | Funkcja/Interfejs | ESP32 Pin (GPIO) | Dodatkowe Informacje |
| :--- | :--- | :--- | :--- |
| **Ethernet (W5500)** | SPI SCK | `GPIO 18` | Hardware SPI |
| **Ethernet (W5500)** | SPI MISO | `GPIO 19` | Hardware SPI |
| **Ethernet (W5500)** | SPI MOSI | `GPIO 23` | Hardware SPI |
| **Ethernet (W5500)** | CS (Chip Select) | `GPIO 5` | |
| **Ethernet (W5500)** | RESET | `GPIO 27` | Soft reset pin |
| **CAN Transceiver** | CAN TX | `GPIO 26` | CAN 2.0B Controller |
| **CAN Transceiver** | CAN RX | `GPIO 25` | |
| **Serwo Kierowania (Przód)** | PWM OUT (SV_A_PIN) | `GPIO 33` | 50Hz, Zakres pulsu: 500-2500 µs |
| **Serwo Kierowania (Tył)** | PWM OUT (SV_B_PIN) | `GPIO 32` | 50Hz, Zakres pulsu: 500-2500 µs |
| **Czujnik Prądu Serwa A**| Analog In (SV_CFB_A) | `GPIO 2` | ADC (12-bit, VREF=3.3V, ACS712) |
| **Czujnik Prądu Serwa B**| Analog In (SV_CFB_B) | `GPIO 15` | ADC (ACS712 5A) |
| **Czujnik Napięcia Serwa A**| Analog In (SV_VFB_A) | `GPIO 0` | ADC dzielnik |
| **Czujnik Napięcia Serwa B**| Analog In (SV_VFB_B) | `GPIO 4` | ADC dzielnik |
| **Status LED** | NeoPixel | `GPIO 7` | Diagnostyka RGB |

---

## 6. Algorytmy Sterowania i Bezpieczeństwo

Kluczowe mechanizmy dbałości o hardware wdrożone w systemie:

1. **Watchdog Bezpieczeństwa (SAFETY_TIMEOUT):** Jeśli ESP32 nie otrzyma poprawnego pakietu MQTT przez więcej niż **1000 ms**, system automatycznie wyzeruje wszystkie pule zmiennych (prędkości i kąty skrętu), zatrzymując pojazd.
2. **PID Skrętu (Steering PID):**
   Aplikacja nie rzuca "skoków" PWM do serwomechanizmów o dużej mocy. Zastosowano programowy PID (Tuning: `Kp = 2.5, Ki = 0.1, Kd = 0.05`), który ogranicza maksymalną prędkość skrętu do `1.5 rad/s` (zabezpieczenie Anti-Windup i ochrona zębatek). Maksymalny odchył mechaniczny `MAX_STEER_RAD` to 1.0 rad.
3. **Estymator Opóźnień (Latency Estimator):**
   Aplikacja bazowa posiada algorytm korelujący wystawioną wartość prędkości docelowej (`push_target`) ze zwróconą pozycją z enkodera, obliczając bieżące opóźnienie w milisekundach (wyświetlane na ekranie diagnostyki w GUI).

---

## 7. Struktura Repozytorium

```text
ORION_VI_PROPULSION_SYSTEM/
├── Base_Application/       # Aplikacja sterująca na komputer (Python)
│   ├── main.py             # Entry point (uruchomienie pętli GUI i MQTT)
│   ├── gui.py              # UI (Tkinter) - wykresy, zegary, dashboard
│   ├── comms.py            # Klasa MqttManager (połączenia, parsowanie JSON)
│   ├── inputs.py           # Klasa InputManager (obsługa pygame joystick)
│   ├── config.py           # Plik z definicjami (IP, tematy, stałe kół/przekładni)
│   └── utils.py            # AppState - wzorzec stanu uwspólnionego + LatencyEstimator
│
└── Low_Level_Code/         # Firmware dla mikrokontrolerów ESP32 (C++/Arduino)
    └── chassis_new/
        ├── chassis_new.ino # Pętla główna sprzętu (inicjalizacja, PID, Watchdog)
        ├── config.h        # Najważniejsze makra, PINY, konfiguracja sprzętu i PID
        ├── Network.cpp/h   # Obsługa SPI Ethernet W5500 oraz klienta MQTT
        └── OdriveCAN.cpp/h # Protokół ODrive (Simple CAN protocol v3.6/v4)
```

---

## 8. Instrukcja Wdrożenia (Deployment)

### Krok 1: Wdrożenie Firmware'u na ESP32
1. Otwórz projekt `chassis_new.ino` w środowisku Arduino IDE / PlatformIO.
2. Wymagane biblioteki: `Ethernet`, `PubSubClient`, `CAN`, `ArduinoJson`, `ESP32Servo`.
3. Przed kompilacją otwórz `config.h` i zdefiniuj `CURRENT_SIDE` na `SIDE_LEFT` lub `SIDE_RIGHT` w zależności od wgrywanego fizycznie modułu.
4. Skompiluj i wgraj oprogramowanie. Zweryfikuj konsolę szeregową (baud: 115200) w poszukiwaniu "CAN Init OK" oraz "[MQTT] Connected!".

### Krok 2: Uruchomienie Stacji Bazowej (PC)
1. Wymagania: `Python 3.10+`.
2. Zainstaluj zależności: `pip install numpy pygame paho-mqtt matplotlib`.
3. Skonfiguruj interfejs sieciowy PC na karcie połączonej do sieci rovera na pulę `192.168.1.x`. Upewnij się, że broker MQTT działa na `192.168.1.1`.
4. Wejdź do katalogu `Base_Application/` i wykonaj: `python main.py`.
5. Interfejs uruchomi się w trybie pełnoekranowym (klawisz `ESC` do wyjścia).

### Krok 3: Inicjalizacja Napędu (Pre-flight)
W GUI wybierz opcje w sekcji *Polecenia ODrive*:
1. `★ FULL START (AUTO) ★` - Wykona zautomatyzowaną sekwencję (Kalibracja -> Czekaj -> Closed Loop -> Tryb Prędkości (Vel Mode)).
2. Po tym układ jest uzbrojony i reaguje na polecenia z Gamepada.
"""

with open("/mnt/data/README.md", "w", encoding="utf-8") as f:
    f.write(content)

print("File generated successfully.")

```
