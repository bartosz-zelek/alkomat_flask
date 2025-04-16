#include <Arduino.h>
#include <MQUnifiedsensor.h>
#include <LiquidCrystal_I2C.h>

#define RatioMQ3CleanAir (60)

MQUnifiedsensor MQ3("Arduino", 5.0F, 10, A0, "MQ-3");
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup()
{
  Serial.begin(9600);

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
  int adc;

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
      if (adc > baseline + 50)
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
          delay(100);
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
    lcd.print(resp);
    delay(2000);
    lcd.clear();
  }
}
