#include <Arduino.h>
// #include <MQUnifiedsensor.h>
// #include <LiquidCrystal_I2C.h>
// #include <ESP32Servo.h>
#include <WiFi.h>
#include "esp_wifi.h"

#define WIFI_SSID "alkomat"
#define WIFI_PASSWORD "aqWSde123"
// #define RatioMQ3CleanAir (60)
// #define BUZZER_PIN 13
// #define SERVO_PIN 15
// #define ALKO_SENSOR_PIN 34

String get_wifi_status(int status)
{
  switch (status)
  {
  case WL_IDLE_STATUS:
    return "WL_IDLE_STATUS";
  case WL_SCAN_COMPLETED:
    return "WL_SCAN_COMPLETED";
  case WL_NO_SSID_AVAIL:
    return "WL_NO_SSID_AVAIL";
  case WL_CONNECT_FAILED:
    return "WL_CONNECT_FAILED";
  case WL_CONNECTION_LOST:
    return "WL_CONNECTION_LOST";
  case WL_CONNECTED:
    return "WL_CONNECTED";
  case WL_DISCONNECTED:
    return "WL_DISCONNECTED";
  default:
    return "WL_UNKNOWN_STATUS";
  }
}

// MQUnifiedsensor MQ3("Arduino", 5.0F, 10, ALKO_SENSOR_PIN, "MQ-3");
// LiquidCrystal_I2C lcd(0x27, 16, 2);
// Servo servo;
// int servoPos = 0; // Variable to store the servo position

bool connectToWifi(const char *ssid, const char *password, int maxAttempts = 5)
{
  Serial.printf("Connecting to SSID: %s\n", ssid);
  
  // Ustawienie trybu stacji przed skanowaniem
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true);
  delay(100);
  
  // Skanowanie dostępnych sieci
  Serial.println("Scanning networks...");
  int n = WiFi.scanNetworks();
  bool openAP = false;
  int foundIndex = -1;
  
  for (int i = 0; i < n; i++) {
    if (WiFi.SSID(i) == String(ssid)) {
      openAP = (WiFi.encryptionType(i) == WIFI_AUTH_OPEN);
      foundIndex = i;
      break;
    }
  }
  
  if (foundIndex >= 0) {
    Serial.printf("Network '%s' found (RSSI %d), type: %s\n",
                  ssid, WiFi.RSSI(foundIndex),
                  openAP ? "OPEN" : "SECURED");
  } else {
    Serial.println("Warning: SSID not found in scan results.");
  }

  int channel = (foundIndex >= 0) ? WiFi.channel(foundIndex) : 0;
  uint8_t bssid[6];
  if (foundIndex >= 0) {
    memcpy(bssid, WiFi.BSSID(foundIndex), 6);
    Serial.printf("BSSID: %02X:%02X:%02X:%02X:%02X:%02X, Channel: %d\n", 
                  bssid[0], bssid[1], bssid[2], bssid[3], bssid[4], bssid[5], channel);
  } else {
    memset(bssid, 0, 6);
  }

  // Włącz automatyczne ponowne łączenie
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);
  
  // Wyłącz oszczędzanie energii
  WiFi.setSleep(false);
  
  // Ustawienie kraju dla poprawnej konfiguracji kanałów 2.4GHz (opcjonalnie)
  #ifdef ESP_PLATFORM
  // To używaj tylko jeśli masz dołączony odpowiedni nagłówek "esp_wifi.h"
  wifi_country_t country = {"PL", 0, 13, WIFI_COUNTRY_POLICY_AUTO};
  esp_wifi_set_country(&country);
  #endif

  int attempt = 0;
  bool connected = false;

  while (attempt < maxAttempts && !connected)
  {
    attempt++;

    Serial.printf("Attempt %d/%d...\n", attempt, maxAttempts);
    
    // Rozłącz przed próbą połączenia
    WiFi.disconnect(true);
    delay(100);
    
    // Open networks: simple begin; secured APs: include channel+BSSID; fallback uses password-only
    if (openAP) {
      Serial.println("Connecting to open AP...");
      WiFi.begin(ssid);
    } else if (foundIndex >= 0) {
      Serial.println("Connecting to secured AP...");
      WiFi.begin(ssid, password, channel, bssid);
    } else {
      Serial.println("Connecting to secured AP (fallback)...");
      WiFi.begin(ssid, password);
    }

    // Dynamiczne opóźnienie rosnące z każdą próbą
    unsigned long timeout = 5000 + (attempt * 2000); // 5s, 7s, 9s...
    unsigned long startAttempt = millis();

    // Czekanie na połączenie
    while (millis() - startAttempt < timeout)
    {
      if (WiFi.status() == WL_CONNECTED)
      {
        connected = true;
        break;
      }
      Serial.print(".");
      delay(500);
    }
    Serial.println();

    if (connected)
    {
      Serial.println("\n✅ WiFi connected!");
      Serial.print("IP address: ");
      Serial.println(WiFi.localIP());
      Serial.print("RSSI: ");
      Serial.println(WiFi.RSSI());
      return true;
    }
    else
    {
      // Używamy standardowego WiFi.status() zamiast getStatusCode
      Serial.printf("❌ Attempt %d failed. Status: %s\n",
                    attempt, get_wifi_status(WiFi.status()).c_str());

      delay(1000);
    }
  }

  Serial.println("\n⚠️ Failed to connect after maximum attempts.");
  return false;
}


void setup()
{
  {
    Serial.begin(9600);
    // Force station mode and clear any old credentials
   connectToWifi(WIFI_SSID, WIFI_PASSWORD);

    // pinMode(SERVO_PIN, OUTPUT);
    // pinMode(BUZZER_PIN, OUTPUT);
    // digitalWrite(BUZZER_PIN, LOW);
  }

  // {
  //   servo.attach(SERVO_PIN);
  //   servo.write(servoPos); // Set initial position to 0 degrees
  //   // Calibrate servo: sweep from 0° to 180° and back
  //   for (int angle = 0; angle <= 180; angle++)
  //   {
  //     servo.write(angle);
  //     delay(10);
  //   }
  //   for (int angle = 180; angle >= 0; angle--)
  //   {
  //     servo.write(angle);
  //     delay(10);
  //   }
  //   servo.write(servoPos); // Return to initial position
  //   servo.detach();        // Detach to stop pulses after calibration
  // }

  // {
  //   // Initialize the LCD
  //   lcd.init(); // Initialize the LCD
  //   lcd.begin(16, 2);
  //   lcd.backlight();
  //   lcd.setCursor(0, 0);
  //   lcd.print("Alcohol Sensor");
  //   delay(2000);
  //   lcd.clear();
  // }

  // {
  //   MQ3.setRegressionMethod(1);
  //   MQ3.setA(0.3934);
  //   MQ3.setB(-1.504); // Configure the equation to to calculate Alcohol concentration
  //   MQ3.init();

  //   if (analogRead(ALKO_SENSOR_PIN) == 0)
  //   {
  //     Serial.println("Warning: Conection issue, R0 is 0 (Open circuit detected) please check your wiring and supply");
  //   }
  // }
}

void loop()
{
  // put your main code here, to run repeatedly:
}
