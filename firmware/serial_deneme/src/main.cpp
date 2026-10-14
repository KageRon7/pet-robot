#include <Arduino.h>
#include <ESP32Servo.h>

Servo myServo;
const int servoPin = 18;

unsigned long previousMillis = 0;   // son hareketin yapıldığı zamanı saklar
const unsigned long interval = 300; // hareketler arası bekleme süresi

int angle = 0;
int step = 10;

void setup()
{
  Serial.begin(115200);
  Serial.println("Merhaba ESP32!");

  myServo.attach(servoPin);
  myServo.write(angle);
}

void loop()
{
  unsigned long currentMillis = millis(); // esp32 açıldıpından beri geçen sürr

  if (currentMillis - previousMillis >= interval) // son hareketten 300ms geçtiyse kod çalısır
  {
    previousMillis = currentMillis;

    myServo.write(angle);
    Serial.print("Aci: ");
    Serial.println(angle);

    angle += step;

    if (angle >= 180 || angle <= 0)
    {
      step = -step;
    }
  }
}