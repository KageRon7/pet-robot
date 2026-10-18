#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// 3 saniye güvenlik sigortası için zaman tutucu değişkenler
unsigned long sonMesajZamani = 0;
bool sigortaDevredeMi = false;

const int NUM_SERVOS = 5;

// S0: govde (tabanda, doner rulman)
// S1: bas sag-sol
// S2: bas yukari-asagi (0 mantiksal = 90 derece)
// S3: sol kulak
// S4: sag kulak 
const int pins[NUM_SERVOS] = {13, 12, 14, 27, 26};

// servonun gidebilecegi gercek aci araligi
const int minAci[NUM_SERVOS] = {45, 0, 80, 60, 30};
const int maxAci[NUM_SERVOS] = {135, 180, 135, 150, 120};

// başta hepsi düz, kulaklar notr (sol 132, sag 48 derece)
const int idleAci[NUM_SERVOS] = {90, 90, 90, 132, 48};

const unsigned long IDLE_RETURN_MS = 800; // donus suresi
const unsigned long UPDATE_INTERVAL = 10; // servo guncelleme araligi

Servo servos[NUM_SERVOS];
float startVal[NUM_SERVOS];   // hareket baslarkenki aci
float targetVal[NUM_SERVOS];  // gidilecek hedef aci
float currentVal[NUM_SERVOS]; // su anki aci

unsigned long moveStart = 0;
unsigned long moveDuration = 0; // hareketin sures
bool moving = false;            // servolar hareket halinde mı
unsigned long lastUpdate = 0;   // servolarin son guncellenme zamani

// Su anki konumdan hedefe, ms surede hareketi baslatir
void hareketBaslat(const float target[], unsigned long ms)
{
  for (int i = 0; i < NUM_SERVOS; i++)
  {
    startVal[i] = currentVal[i];
    targetVal[i] = target[i];
  }
  moveStart = millis();
  moveDuration = ms;
  moving = true;
}

// Servolari pine baglar ve duz konuma getirir, setup'ta bir kez cagrilir
void eda_Baslat()
{
  ESP32PWM::allocateTimer(0); // servo PWM zamanlayicilarini
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    servos[i].attach(pins[i], 500, 2400); // servoyu pine bagla
    currentVal[i] = idleAci[i];           // baslangicta duz durusta
    startVal[i] = idleAci[i];
    targetVal[i] = idleAci[i];
    servos[i].write(idleAci[i]); // servoyu duz konuma getir
  }
}

// Zamana dayali yumusak hareket, loop'ta surekli cagrilir
void servoGuncelle() // tum servolar ayni anda baslar ve ayni anda biter
{
  if (!moving)
    return;

  unsigned long now = millis();
  if (now - lastUpdate < UPDATE_INTERVAL)
    return;
  lastUpdate = now;

  // t: hareketin yuzde kaci tamamlandi 0-1
  float t = (moveDuration == 0) ? 1.0f : (float)(now - moveStart) / moveDuration;
  if (t >= 1.0f)
  {
    t = 1.0f;
    moving = false;
  }

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    currentVal[i] = startVal[i] + (targetVal[i] - startVal[i]) * t; // ara aci
    servos[i].write((int)roundf(currentVal[i]));                    // servoya gonder
  }
}

// 1. "move" komutu geldiğinde 5 servonun hedef açısını (S0-S4) ve süreyi (ms) Eda'ya verir
void eda_HedefeGit(int hedefAcilar[5], int sure_ms)
{
  float target[NUM_SERVOS];
  for (int i = 0; i < NUM_SERVOS; i++)
  {
    target[i] = constrain(hedefAcilar[i], minAci[i], maxAci[i]); // servo siniri disina cikma
  }
  hareketBaslat(target, sure_ms); // harekete baslar
}

// 2. "neutral" komutu geldiğinde veya 3 sn sigortası attığında Eda motorları nötre çeker
void eda_NotreDon()
{
  float target[NUM_SERVOS];
  for (int i = 0; i < NUM_SERVOS; i++)
  {
    target[i] = idleAci[i];
  }
  hareketBaslat(target, IDLE_RETURN_MS); // duz durusa doner
}
// 1. "move" komutu geldiğinde 5 servonun hedef açısını (S0-S4) ve süreyi (ms) Eda'ya verir
void eda_HedefeGit(int hedefAcilar[5], int sure_ms) {
  // Eda burada millis() kullanarak 5 servoyu sure_ms içinde hedefAcilar'a götürecek.
}

// 2. "neutral" komutu geldiğinde veya 3 sn sigortası attığında Eda motorları nötre çeker
void eda_NotreDon() {
  // Eda burada tüm servoları başlangıç (nötr) açılarına götürecek.
}
// =========================================================================


// Bilgisayara Başarılı ("aldım") Cevabı Gönderen Fonksiyon -> {"ack":42,"ok":true}
void ackGonder(int seqNumarasi) {
  StaticJsonDocument<64> doc;
  doc["ack"] = seqNumarasi;
  doc["ok"] = true;
  serializeJson(doc, Serial);
  Serial.println(); // Sözleşme kuralı: Her mesaj \n (yeni satır) ile bitmeli
}

// Bilgisayara Hatalı Cevap Gönderen Fonksiyon -> {"ack":42,"ok":false,"err":"bad_json"}
void hataGonder(int seqNumarasi, const char* hataKodu) {
  StaticJsonDocument<96> doc;
  doc["ack"] = seqNumarasi;
  doc["ok"] = false;
  doc["err"] = hataKodu; // "bad_json", "bad_cmd" veya "out_of_range"
  serializeJson(doc, Serial);
  Serial.println();
}

void setup() {
  Serial.begin(115200); // Sözleşme C2 kuralı: Baud hızı 115200
  sonMesajZamani = millis();
    eda_Baslat();
}

void loop() {
  // 1. SERİ PORTTAN MESAJ GELDİ Mİ KONTROL ET
    servoGuncelle();
  if (Serial.available() > 0) {
    String gelenSatir = Serial.readStringUntil('\n'); // Satır sonuna kadar oku
    gelenSatir.trim(); // Başındaki ve sonundaki boşlukları temizle

    if (gelenSatir.length() > 0) {
      StaticJsonDocument<256> doc;
      DeserializationError error = deserializeJson(doc, gelenSatir);

      // KURAL 1: Gelen metin bozuk bir JSON ise "bad_json" hatası dön
      if (error) {
        hataGonder(-1, "bad_json");
        return;
      }

      // Mesaj sıra numarasını (seq) ve komutu (cmd) oku
      int seq = doc["seq"] | -1; 
      const char* cmd = doc["cmd"];

      // Komut alanı hiç yazılmamışsa "bad_cmd" hatası dön
      if (cmd == nullptr) {
        hataGonder(seq, "bad_cmd");
        return;
      }

      // KURAL 2: "ping" komutu (Bilgisayar bağlantıyı kontrol ediyor)
      if (strcmp(cmd, "ping") == 0) {
        sonMesajZamani = millis();
        sigortaDevredeMi = true;
        ackGonder(seq);
      }
      // KURAL 3: "neutral" komutu (Motorları nötr pozisyona al)
      else if (strcmp(cmd, "neutral") == 0) {
        sonMesajZamani = millis();
        sigortaDevredeMi = true;
        eda_NotreDon(); // Eda'nın fonksiyonunu çağır
        ackGonder(seq);
      }
      // KURAL 4: "move" komutu (Motorları verilen açılara götür)
      else if (strcmp(cmd, "move") == 0) {
        // "deg" (açılar) veya "ms" (süre) alanı eksikse hata dön
        if (!doc.containsKey("deg") || !doc.containsKey("ms")) {
          hataGonder(seq, "bad_cmd");
          return;
        }

        JsonArray degArray = doc["deg"].as<JsonArray>();
        int ms = doc["ms"];

        // 5 servo açısı yoksa veya süre negatifse "out_of_range" hatası dön
        if (degArray.size() != 5 || ms < 0) {
          hataGonder(seq, "out_of_range");
          return;
        }

        int acilar[5];
        for (int i = 0; i < 5; i++) {
          acilar[i] = degArray[i];
          // Açılar 0 ile 180 derece arasında değilse "out_of_range" hatası dön
          if (acilar[i] < 0 || acilar[i] > 180) {
            hataGonder(seq, "out_of_range");
            return;
          }
        }

        // Her şey doğru! Sigorta süresini sıfırla, Eda'ya inputları ver ve "ack" gönder
        sonMesajZamani = millis();
        sigortaDevredeMi = true;

        eda_HedefeGit(acilar, ms);
        ackGonder(seq);
      }
      // Sözleşmede olmayan bir komut geldiyse ("bad_cmd")
      else {
        hataGonder(seq, "bad_cmd");
      }
    }
  }

  // 2. 3 SANİYE GÜVENLİK SİGORTASI
  // Son geçerli mesajdan bu yana 3000 ms (3 saniye) geçtiyse motorları nötre çek
  if (sigortaDevredeMi && (millis() - sonMesajZamani > 3000)) {
    eda_NotreDon();
    sigortaDevredeMi = false; 
  }
}
