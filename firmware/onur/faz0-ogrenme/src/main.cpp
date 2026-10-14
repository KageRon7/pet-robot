#include <Arduino.h>        // Arduino'nun temel fonksiyonları (Serial, constrain vb.)
#include <ArduinoJson.h>    // Gelen metni JSON olarak okuyan kütüphane
#include <ESP32Servo.h>     // ESP32'de servo motoru döndüren kütüphane

Servo servo;                // "servo" adında bir servo nesnesi oluşturur

void setup() {              // Açılışta bir kez çalışır
  Serial.begin(115200);     // Bilgisayarla seri haberleşmeyi 115200 hızında başlatır
  servo.attach(18);         // Servonun sinyal kablosunu GPIO18 pinine bağlar
  servo.write(90);          // Başlangıçta servoyu ortaya (90 derece) getirir
  Serial.println("Hazir. Ornek: {\"angle\": 45}");  // Kullanıcıya örnek mesajı gösterir
}

void loop() {               // Sürekli tekrar eder
  if (!Serial.available()) return;  // Gelen veri yoksa bu turu bitir, bekle

  String line = Serial.readStringUntil('\n');  // Enter'a kadar gelen metni okur
  line.trim();              // Baştaki ve sondaki boşlukları/gizli karakterleri siler
  if (line.length() == 0) return;  // Satır boşsa hiçbir şey yapma

  JsonDocument doc;         // Ayrıştırılan JSON'un saklanacağı kutu
  DeserializationError err = deserializeJson(doc, line);  // Metni JSON'a çevirmeyi dener
  if (err) {                // Çevirme başarısızsa (bozuk JSON)
    Serial.println("hata: gecersiz json");  // Hata cevabı gönder
    return;                 // Bu turu bitir, servoya dokunma
  }

  int angle = doc["angle"] | 90;   // "angle" değerini al, yoksa 90 kullan
  angle = constrain(angle, 0, 180);  // Açıyı 0-180 arasında tut (servoyu korur)
  servo.write(angle);       // Servoyu o açıya döndür
  Serial.print("ok angle=");  // Cevabın ilk kısmını yaz (satır atlamadan)
  Serial.println(angle);    // Açıyı yaz ve satır atla
}