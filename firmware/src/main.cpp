#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// --- GÜVENLİK VE İLETİŞİM DEĞİŞKENLERİ ---
unsigned long sonMesajZamani = 0;
bool sigortaDevredeMi = false;
String gelenSatir = ""; // Klavyeden yazılan karakterleri biriktirme hafızası

// --- SERVO VE HAREKET DEĞİŞKENLERİ (Eda'nın Altyapısı) ---
const int NUM_SERVOS = 5;
const int pins[NUM_SERVOS] = {13, 12, 14, 27, 26};

// Servonun gidebileceği fiziksel açı sınırları
const int minAci[NUM_SERVOS] = {45, 0, 80, 60, 30};
const int maxAci[NUM_SERVOS] = {135, 180, 135, 150, 120};

// Başlangıç/Nötr açıları
const int idleAci[NUM_SERVOS] = {90, 90, 90, 132, 48};

const unsigned long IDLE_RETURN_MS = 800; // Nötre dönüş süresi
const unsigned long UPDATE_INTERVAL = 10; // Servo güncelleme aralığı

Servo servos[NUM_SERVOS];
float startVal[NUM_SERVOS];   // Hareket başlarkenki açı
float targetVal[NUM_SERVOS];  // Gidilecek hedef açı
float currentVal[NUM_SERVOS]; // Şu anki açı

unsigned long moveStart = 0;
unsigned long moveDuration = 0; 
bool moving = false;            
unsigned long lastUpdate = 0;   

// =========================================================================
// HAREKET VE MOTOR FONKSİYONLARI
// =========================================================================

void hareketBaslat(const float target[], unsigned long ms) {
  for (int i = 0; i < NUM_SERVOS; i++) {
    startVal[i] = currentVal[i];
    targetVal[i] = target[i];
  }
  moveStart = millis();
  moveDuration = ms;
  moving = true;
}

void motorlariBaslat() {
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(pins[i], 500, 2400); 
    currentVal[i] = idleAci[i];           
    startVal[i] = idleAci[i];
    targetVal[i] = idleAci[i];
    servos[i].write(idleAci[i]); 
  }
}

void servoGuncelle() {
  if (!moving) return;

  unsigned long now = millis();
  if (now - lastUpdate < UPDATE_INTERVAL) return;
  lastUpdate = now;

  float t = (moveDuration == 0) ? 1.0f : (float)(now - moveStart) / moveDuration;
  if (t >= 1.0f) {
    t = 1.0f;
    moving = false;
  }

  for (int i = 0; i < NUM_SERVOS; i++) {
    currentVal[i] = startVal[i] + (targetVal[i] - startVal[i]) * t; 
    servos[i].write((int)roundf(currentVal[i]));                    
  }
}

void hedefAcilaraGit(int hedefAcilar[5], int sure_ms) {
  float target[NUM_SERVOS];
  for (int i = 0; i < NUM_SERVOS; i++) {
    // Ekstra donanım güvenliği için constrain (Sınır dışı zaten JSON'da reddedilecek)
    target[i] = constrain(hedefAcilar[i], minAci[i], maxAci[i]); 
  }
  hareketBaslat(target, sure_ms); 
}

void notrPozisyonaDon() {
  float target[NUM_SERVOS];
  for (int i = 0; i < NUM_SERVOS; i++) {
    target[i] = idleAci[i];
  }
  hareketBaslat(target, IDLE_RETURN_MS); 
}

// =========================================================================
// İLETİŞİM FONKSİYONLARI
// =========================================================================

void ackGonder(int seqNumarasi) {
  StaticJsonDocument<64> doc;
  doc["ack"] = seqNumarasi;
  doc["ok"] = true;
  serializeJson(doc, Serial);
  Serial.println(); 
}

void hataGonder(int seqNumarasi, const char* hataKodu) {
  StaticJsonDocument<96> doc;
  doc["ack"] = seqNumarasi;
  doc["ok"] = false;
  doc["err"] = hataKodu; 
  serializeJson(doc, Serial);
  Serial.println();
}

void setup() {
  Serial.begin(115200); 
  sonMesajZamani = millis();
  motorlariBaslat();
}

void loop() {
  // 1. Motorların yumuşak hareketini devam ettir
  servoGuncelle();

  // 2. Seri porttan mesaj oku (Echo destekli)
  while (Serial.available() > 0) {
    char c = Serial.read();
    Serial.print(c); // Yazılanı ekrana geri yansıt

        if (c == '\n' || c == '\r') {
      gelenSatir.trim();

      if (gelenSatir.length() > 0) {
        Serial.println(); // Okunabilirlik için alt satıra geç

        StaticJsonDocument<256> doc;
        DeserializationError error = deserializeJson(doc, gelenSatir);

        if (error) {
          hataGonder(-1, "bad_json");
        } else {
          int seq = doc["seq"] | -1; 
          const char* cmd = doc["cmd"];

          if (cmd == nullptr) {
            hataGonder(seq, "bad_cmd");
          }
          else if (strcmp(cmd, "ping") == 0) {
            sonMesajZamani = millis();
            sigortaDevredeMi = true;
            ackGonder(seq);
          }
          else if (strcmp(cmd, "neutral") == 0) {
            sonMesajZamani = millis();
            sigortaDevredeMi = true;
            notrPozisyonaDon(); 
            ackGonder(seq);
          }
          else if (strcmp(cmd, "move") == 0) {
            if (!doc.containsKey("deg") || !doc.containsKey("ms")) {
              hataGonder(seq, "bad_cmd");
            } else {
              JsonArray degArray = doc["deg"].as<JsonArray>();
              int ms = doc["ms"];

              if (degArray.size() != 5 || ms < 0) {
                hataGonder(seq, "out_of_range");
              } else {
                int acilar[5];
                bool sinirDisi = false;

                // Açıları Eda'nın belirlediği fiziksel sınırlarla test et
                for (int i = 0; i < 5; i++) {
                  acilar[i] = degArray[i];
                  if (acilar[i] < minAci[i] || acilar[i] > maxAci[i]) {
                    sinirDisi = true;
                  }
                }
                
                if (sinirDisi) {
                  hataGonder(seq, "out_of_range");
                } else {
                  sonMesajZamani = millis();
                  sigortaDevredeMi = true;
                  hedefAcilaraGit(acilar, ms);
                  ackGonder(seq);
                }
              }
            }
          }
          else {
            hataGonder(seq, "bad_cmd");
          }
        }
      }
      gelenSatir = ""; // Bir sonraki komut için temizle
    }
    else {
      gelenSatir += c;
    }
  }

  // 3. Güvenlik Sigortası (3 sn boyunca ping gelmezse nötre dön)
  if (sigortaDevredeMi && (millis() - sonMesajZamani > 3000)) {
    notrPozisyonaDon();
    sigortaDevredeMi = false; 
  }
}