#include <Arduino.h>
#include <MQUnifiedsensor.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>
#include <UUID.h>

#define RatioMQ3CleanAir (60)
#define BUZZER_PIN 12 // Pin for the speaker/buzzer
#define SERVO_PIN A2  // Pin for the servo motor

MQUnifiedsensor MQ3("Arduino", 5.0F, 10, A0, "MQ-3");
LiquidCrystal_I2C lcd(0x27, 16, 2);
Servo servo;
int servoPos = 0; // Variable to store the servo position
int adc;
String brethalyzerId;
UUID uuid;


void setup()
{
  Serial.begin(9600);

  // insert brethalyzer id
  {
    while (!Serial)
      ;                      // wait for USB-serial to come up
    Serial.setTimeout(5000); // wait up to 5s for the user to type
    brethalyzerId = Serial.readStringUntil('\n');
    brethalyzerId.trim(); // drop CR/LF
    // flush any extra bytes so loop() gets only new data
    while (Serial.available())
    {
      Serial.read();
    }
  }

  {
    pinMode(SERVO_PIN, OUTPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW); // Turn off the buzzer initially
  }

  {
    servo.attach(SERVO_PIN);
    servo.write(servoPos); // Set initial position to 0 degrees
    // Calibrate servo: sweep from 0° to 180° and back
    for (int angle = 0; angle <= 180; angle++)
    {
      servo.write(angle);
      delay(10);
    }
    for (int angle = 180; angle >= 0; angle--)
    {
      servo.write(angle);
      delay(10);
    }
    servo.write(servoPos); // Return to initial position
    servo.detach();        // Detach to stop pulses after calibration
  }

  {
    // Initialize the LCD
    lcd.init(); // Initialize the LCD
    lcd.begin(16, 2);
    lcd.backlight();
    lcd.setCursor(0, 0);
    lcd.print("Alcohol Sensor");
    delay(2000);
    lcd.clear();
  }

  {
    MQ3.setRegressionMethod(1);
    MQ3.setA(0.3934);
    MQ3.setB(-1.504); // Configure the equation to to calculate Alcohol concentration
    MQ3.init();

    // Serial.print("Calibrating please wait.");
    float calcR0 = 0;
    for (int i = 1; i <= 10; i++)
    {
      MQ3.update(); // Update data, the arduino will read the voltage from the analog pin
      calcR0 += MQ3.calibrate(RatioMQ3CleanAir);
      // Serial.print(".");
    }
    MQ3.setR0(calcR0 / 10);
    // Serial.println("  done!.");

    if (isinf(calcR0))
    {
      Serial.println("Warning: Conection issue, R0 is infinite (Open circuit detected) please check your wiring and supply");
      while (1)
        ;
    }
    if (calcR0 == 0)
    {
      Serial.println("Warning: Conection issue found, R0 is zero (Analog pin shorts to ground) please check your wiring and supply");
      while (1)
        ;
    }
  }
}

void loop()
{
  lcd.setCursor(0, 0);
  lcd.print("Recognizing face");

  delay(10000); // Simulate face recognition delay

  uuid.generate();
  String uuidStr = uuid.toCharArray();
  Serial.println(uuidStr); 

  // read from serial
  if (Serial.available())
  {
    String user_id = Serial.readString();
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("User ID: ");
    lcd.print(user_id);
    lcd.setCursor(0, 1);
    lcd.print("Blow to test");

    // Baseline measurement
    int baseline = 0;
    for (int i = 0; i < 10; i++)
    {
      baseline += analogRead(A7);
      delay(50);
    }
    baseline /= 10;
    float maxAdc = baseline;

    // Wait for blow
    bool blowDetected = false;
    while (!blowDetected)
    {
      // clear second row
      MQ3.update();
      adc = analogRead(A7);

      lcd.setCursor(0, 1);

      // Detect blow: threshold can be tuned
      if (adc > baseline + 25 || adc < baseline - 25)
      {
        blowDetected = true;
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Keep blowing...");
        delay(250);

        // Measure for 5 seconds and take max result
        unsigned long measureStart = millis();
        while (millis() - measureStart < 5000)
        {
          MQ3.update();
          adc = analogRead(A7);
          if (adc > maxAdc)
          {
            maxAdc = adc;
          }
          lcd.setCursor(0, 1);
          lcd.print("ADC: ");
          lcd.print(adc);
          lcd.print("    "); // Clear any leftover chars
          delay(50);
        }
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Max ADC: ");
        lcd.print(maxAdc, 0);
        delay(3000);
      }
      delay(100);
    }
    lcd.clear();
    Serial.println((int)maxAdc);
    String resp = Serial.readString();
    lcd.setCursor(0, 0);
    lcd.print("Response: ");
    lcd.setCursor(0, 1);
    lcd.print(resp);
    if (resp == "ACCEPTED")
    {
      servo.attach(SERVO_PIN); // Re-attach before moving
      servoPos = 90;           // Move servo by 90 degrees
      servo.write(servoPos);   // Move the servo to the new position
      digitalWrite(LED_BUILTIN, HIGH);
      delay(5000);                    // Wait for 5 seconds
      digitalWrite(LED_BUILTIN, LOW); // Turn off the built-in LED
      servoPos = 0;                   // Move servo back to original (0°) position
      servo.write(servoPos);          // Move the servo to the new position
      delay(500);                     // Wait for servo to reach original position before detaching
      servo.detach();                 // Detach after movement to prevent ticking
    }
    else
    {
      // make sound
      // blink with builtin led
      for (int i = 0; i < 5; i++)
      {
        digitalWrite(LED_BUILTIN, HIGH); // Turn on the built-in LED
        digitalWrite(BUZZER_PIN, HIGH);  // Turn on the buzzer
        delay(500);                      // Wait for 0.5 seconds
        digitalWrite(LED_BUILTIN, LOW);  // Turn off the built-in LED
        digitalWrite(BUZZER_PIN, LOW);   // Turn off the buzzer
        delay(500);                      // Wait for 0.5 seconds
      }
      digitalWrite(BUZZER_PIN, LOW); // Turn off the buzzer
    }
    delay(2000);
    lcd.clear();
  }
}
