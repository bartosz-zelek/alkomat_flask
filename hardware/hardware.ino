#include <Servo.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>
#include <OneWire.h>

#define RST_PIN 9
#define SS_PIN 10
#define LCD_ADDR 0x27
#define SENSOR_PIN A0
#define BTN_PIN 2
#define SERVO_PIN 3

MFRC522 mfrc522(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(LCD_ADDR, 16,2);
Servo servo;

char com = 0;
int ref_val = 0;
int meas_val = 0;
float scaled_val = 0;

// simple measurement
int measure() {
  int sum = 0;
  int max = 0;
  int min = 1023;
  int meas = 0;
  for (int i = 0; i < 34; i++) {
    meas = analogRead(SENSOR_PIN);
    if (meas < min) min = meas;
    if (meas > max) max = meas;
    sum += meas;
    delay(100);
  }
  sum = sum - min - max;
  sum = sum >> 5;
  return sum;
}

void open_door() {
  // goes from 170deg to 0deg in steps of 1deg
  for (int pos = 180; pos > 0; pos -= 1) { 
    servo.write(pos);
    delay(15); // wait to reach a pos
  }
}

void close_door() {
  // goes from 0deg to 180deg in steps of 1deg
  for (int pos = 0; pos < 180; pos += 1) { 
    servo.write(pos);
    delay(15); // wait to reach a pos
  }
}

void setup() {
  pinMode(SENSOR_PIN, INPUT);
  pinMode(BTN_PIN, INPUT_PULLUP);
  // pinMode(7, OUTPUT);
  // pinMode(8, OUTPUT);
  Serial.begin(9600);
  delay(1000);  
  SPI.begin();
  mfrc522.PCD_Init();
  servo.attach(SERVO_PIN);
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0,0);
  lcd.print("Zeskanuj karte  ");
}

void loop() {
  // check for new RFID card
  if ( mfrc522.PICC_IsNewCardPresent()) {
    if ( mfrc522.PICC_ReadCardSerial()) {
      // get ref. val.
      ref_val = measure();
      for (byte i = 0; i < mfrc522.uid.size; i++) {
        Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
        Serial.print(mfrc522.uid.uidByte[i], HEX);
      }
      Serial.print("\n");
      mfrc522.PICC_HaltA();
      // digitalWrite(7, HIGH);
      lcd.setCursor(0,0);
      lcd.print("Wcisnij przycisk");
      lcd.setCursor(0,1);
      lcd.print("po czym dmuchaj ");
      // wait for button press
      while (digitalRead(BTN_PIN)) {}
      meas_val = measure();
      // digitalWrite(7, LOW);
      // scaled_val = scaled_measure(meas_val, ref_val);
      Serial.println(ref_val);
      Serial.println(meas_val);
      lcd.clear();
      // lcd.setCursor(0,0);
      lcd.print("Czekaj          ");
      // wait for serial
      while (Serial.available() <= 0) {}
      com = Serial.read();
      lcd.clear();

      // servo
      switch (com) {
        case 'g':
          lcd.print("Zapraszamy!   ");
          open_door();
          delay(10000);
          close_door();
          lcd.clear();
          break;
        case 'r':
          lcd.print("Jestes pijany:");
          lcd.setCursor(0,1);
          lcd.print("zablokowano.");
          break;
        case 'b':
          lcd.print("Jestes juz    ");
          lcd.setCursor(0,1);
          lcd.print("zablokowany.");
          break;
        case 'n':
          lcd.print("RFID          ");
          lcd.setCursor(0,1);
          lcd.print("nierozpoznane.");
          break;
        default:
          lcd.print("Error.........");
      }
      // clear output
      while (Serial.available() > 0) {
        com = Serial.read();
        }
      delay(1000);
      lcd.clear();
      lcd.print("Zeskanuj karte  ");
    }
  }
}
