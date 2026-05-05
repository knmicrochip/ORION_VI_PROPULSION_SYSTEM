**

---

## 🧩 Moduły Główne

### Aplikacja Bazowa (Python)
Aplikacja stworzona w języku Python (kompatybilna z Python 3.10), zapewniająca stację kontroli dla układu napędowego.
* **`gui.py`**: Definiuje interfejs graficzny, umożliwiając operatorowi odczyt parametrów na żywo.
* **`comms.py`**: Odpowiada za bezpieczne i niezawodne przesyłanie pakietów danych między stacją bazową a łazikiem.
* **`inputs.py`**: Tłumaczy sygnały z urządzeń sterujących (np. joysticków) na komendy zrozumiałe dla układu napędowego.

### Kod Niskopoziomowy (C++/Arduino)
Oprogramowanie mikrokontrolera odpowiedzialne za fizyczne wykonanie poleceń.
* **`OdriveCAN.cpp` & `OdriveCAN.h`**: Dedykowane klasy do obsługi kontrolerów silników bezszczotkowych (BLDC) ODrive przy użyciu wydajnej magistrali CAN.
* **`Network.cpp` & `Network.h`**: Zarządzanie protokołami sieciowymi w celu odbierania komend z `Base_Application`.
* **`chassis_new.ino`**: Pętla główna programu spinająca logikę napędu, odczyty z czujników oraz komunikację.

---

## 🛠 Wymagania

**Dla Aplikacji Bazowej:**
* Python 3.10 lub nowszy
* Wymagane pakiety Python (należy uzupełnić na podstawie faktycznych importów, np. `PyQt5`/`Tkinter`, biblioteki do pada).

**Dla Kodu Niskopoziomowego:**
* Środowisko Arduino IDE lub PlatformIO.
* Mikrokontroler wspierający protokół CAN oraz łączność sieciową (np.Oto propozycja poprawionego i profesjonalnego pliku `README.md` dla Twojego projektu, oparta na strukturze plików, którą udostępniłeś[cite: 1]. Podzieliłem opis na logiczne sekcje, aby ułatwić zrozumienie architektury systemu, która składa się z aplikacji bazowej na PC oraz kodu niskopoziomowego.

---

# 🚀 ORION VI Propulsion System

**ORION VI Propulsion System** to kompleksowe oprogramowanie sterujące i monitorujące układ napędowy łazika/pojazdu[cite: 1]. System charakteryzuje się architekturą rozproszoną, składającą się z wysokopoziomowej aplikacji z graficznym interfejsem użytkownika (GUI) do zdalnego zarządzania[cite: 1] oraz oprogramowania niskopoziomowego, bezpośrednio kontrolującego sprzęt za pośrednictwem magistrali CAN (w tym kontrolery silników ODrive)[cite: 1].

## 📑 Spis treści
* [Architektura Systemu](#architektura-systemu)
* [Struktura Repozytorium](#struktura-repozytorium)
* [Moduły Główne](#moduły-główne)
  * [Aplikacja Bazowa (Python)](#aplikacja-bazowa-python)
  * [Kod Niskopoziomowy (C++/Arduino)](#kod-niskopoziomowy-c-arduino)
* [Wymagania](#wymagania)

---

## 🏗 Architektura Systemu

System podzielony jest na dwie główne warstwy:
1. **High-Level (PC):** Napisana w języku Python aplikacja bazowa z GUI, odpowiedzialna za przetwarzanie danych wejściowych, wyświetlanie telemetrii oraz komunikację ze sterownikiem głównym[cite: 1].
2. **Low-Level (Embedded):** Oprogramowanie układowe (firmware) oparte na języku C++, które zarządza komunikacją sieciową i bezpośrednio steruje sprzętem (np. kontrolerami ODrive) za pomocą protokołu CAN[cite: 1].

---

## 📂 Struktura Repozytorium
```text
ORION_VI_PROPULSION_SYSTEM/
│
├── Base_Application/       # Wysokopoziomowa aplikacja sterująca (Python)
│   ├── main.py             # Główny punkt wejścia aplikacji
│   ├── gui.py              # Logika interfejsu graficznego użytkownika
│   ├── comms.py            # Moduł komunikacji (np. z warstwą Low-Level)
│   ├── inputs.py           # Obsługa urządzeń wejściowych (np. pad, klawiatura)
│   ├── config.py           # Plik konfiguracyjny aplikacji
│   ├── utils.py            # Funkcje pomocnicze
│   └── screenshot_app.png  # Zrzut ekranu aplikacji GUI
│
├── Low_Level_Code/         # Kod mikrokontrolera (C++/Arduino)
│   └── chassis_new/        # Główny program dla układu jezdnego
│       ├── chassis_new.ino # Główny plik projektu Arduino
│       ├── Network.cpp/.h  # Obsługa połączeń sieciowych
│       ├── OdriveCAN.cpp/.h# Biblioteka do komunikacji z ODrive po CAN
│       └── config.h        # Konfiguracja pinów i parametrów sprzętowych
│
└── README.md               # Dokumentacja projektu
## 📜 License

This project is open-source. Feel free to modify and adapt it to your specific robot chassis.
