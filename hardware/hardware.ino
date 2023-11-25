#include "MFRC522.h"
#define RST_PIN 9
#define SS_PIN 10

MFRC522 mfrc522(SS_PIN, RST_PIN);

char com = 0;
int ref_val = 0;
int meas_val = 0;
int scaled_val = 0;

// simple measurement
int measure() {
  int sum = 0;
  int max = 0;
  int min = 1023;
  int meas = 0;
  for (int i = 0; i < 18; i++) {
    meas = analogRead(A5);
    if (meas < min) min = meas;
    if (meas > max) max = meas;
    sum += meas;
    delay(100);
  }
  sum = sum - min - max;
  sum = sum >> 4;
  return sum;
}

// scale = 1 for per cent, 10 for per mille etc.
// normalization assumed as: norm: [-refval;0] -> [0;scale]
// normal scale: c. 80 -> 0 per mille and 0 -> 10 per mille
// realistically the measurement shouldn't be lower than c. 40
int scaled_measure(int xval, int refval, int scale = 10) {
  float xprim = (float) 1 - xval/refval;
  return (int) scale * xprim;
}

void setup() {
  pinMode(A5, INPUT);
  pinMode(2, INPUT_PULLUP);
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  Serial.begin(9600);
  delay(1000);  
  SPI.begin();
  mfrc522.PCD_Init();
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
      // wait for button press
      while (digitalRead(2)) {}
      meas_val = measure();
      scaled_val = scaled_measure(meas_val, ref_val, 10);
      Serial.println(scaled_val);
      delay(1000);
      // wait for serial
      while (Serial.available() <= 0) {}
      com = Serial.read();

      // servo
      if (com == 'g') {
        digitalWrite(7, HIGH);
        delay(1000);
        digitalWrite(7, LOW);
      }
      if (com == 'r') {
        digitalWrite(8, HIGH);
        delay(1000);
        digitalWrite(8, LOW);
      }
      // clear output
      while (Serial.available() > 0) {
        com = Serial.read();
        }
    }
  }
}
