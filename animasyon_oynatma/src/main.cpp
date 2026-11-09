
#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <math.h>
#include <string.h>
#include "animasyonlar.h"

// =====================================================
// SERVO AYARLARI
// =====================================================

const int NUM_SERVOS = 5;

const int pins[NUM_SERVOS] = {13, 12, 14, 27, 26};

const int minAci[NUM_SERVOS] = {45, 0, 80, 60, 30};
const int maxAci[NUM_SERVOS] = {135, 180, 135, 150, 120};

const float idleAci[NUM_SERVOS] = {90, 90, 90, 132, 48};

const unsigned long UPDATE_INTERVAL = 10;

Servo servos[NUM_SERVOS];

float currentVal[NUM_SERVOS];
float startVal[NUM_SERVOS];
float targetVal[NUM_SERVOS];

unsigned long moveStart = 0;
unsigned long moveDuration = 0;
unsigned long lastServoUpdate = 0;

bool moving = false;

// =====================================================
// TFT EKRAN AYARLARI
// =====================================================

#define TFT_CS 5
#define TFT_DC 2
#define TFT_RST 4

#define TFT_SCK 18
#define TFT_MISO 19
#define TFT_MOSI 23

Adafruit_ILI9341 tft(TFT_CS, TFT_DC, TFT_RST);

uint16_t cZemin, cCizgi, cIris;
uint16_t cPembe, cGozyasi, cBeyaz, cKirmizi;

// =====================================================
// ANİMASYON DEĞİŞKENLERİ
// =====================================================

const int MAX_KEY = 100;

Anahtar keys[MAX_KEY];

int keySayisi = 0;
int suankiKlip = -1;

unsigned long klipSuresi = 0;
unsigned long klipBaslangic = 0;
unsigned long sonCizim = 0;

bool klipDongu = false;
bool oynuyor = false;
bool demoModu = false;

const unsigned long FRAME_INTERVAL = 33;

// =====================================================
// SERİ HABERLEŞME VE GÜVENLİK
// =====================================================

unsigned long sonMesajZamani = 0;
bool sigortaDevredeMi = false;

const unsigned long SIGORTA_SURESI = 3000;

char serialBuffer[512];
int serialIndex = 0;

// =====================================================
// GENEL YARDIMCI FONKSİYONLAR
// =====================================================

float sinirla(float deger, float alt, float ust)
{
  if (deger < alt)
    return alt;

  if (deger > ust)
    return ust;

  return deger;
}

float ara(float a, float b, float u)
{
  return a + (b - a) * u;
}

// =====================================================
// SERVO KONTROLÜ
// =====================================================

void hareketBaslat(const float hedef[], unsigned long sure)
{
  for (int i = 0; i < NUM_SERVOS; i++)
  {
    startVal[i] = currentVal[i];
    targetVal[i] = sinirla(hedef[i], minAci[i], maxAci[i]);
  }

  moveStart = millis();
  moveDuration = sure;
  lastServoUpdate = 0;
  moving = true;
}

void eda_Baslat()
{
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    servos[i].setPeriodHertz(50);
    servos[i].attach(pins[i], 500, 2400);

    currentVal[i] = idleAci[i];
    startVal[i] = idleAci[i];
    targetVal[i] = idleAci[i];

    servos[i].write((int)idleAci[i]);
  }

  Serial.println("Servolar baslatildi!");
}

void servoGuncelle()
{
  if (!moving)
    return;

  unsigned long now = millis();

  if (now - lastServoUpdate < UPDATE_INTERVAL)
    return;

  lastServoUpdate = now;

  float u;

  if (moveDuration == 0)
    u = 1.0f;
  else
    u = (float)(now - moveStart) / moveDuration;

  if (u >= 1.0f)
  {
    u = 1.0f;
    moving = false;
  }

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    currentVal[i] = ara(startVal[i], targetVal[i], u);
    servos[i].write((int)roundf(currentVal[i]));
  }
}

void eda_NotreDon()
{
  hareketBaslat(idleAci, 800);
}

void eda_HedefeGit(int hedefAcilar[5], int sure)
{
  float hedef[NUM_SERVOS];

  for (int i = 0; i < NUM_SERVOS; i++)
    hedef[i] = hedefAcilar[i];

  hareketBaslat(hedef, sure);
}

// =====================================================
// JSON AĞIZ VE EASING
// =====================================================

int agizNo(const char *s)
{
  if (strcmp(s, "smile") == 0)
    return 1;

  if (strcmp(s, "frown") == 0)
    return 2;

  if (strcmp(s, "wavy") == 0)
    return 3;

  if (strcmp(s, "zigzag") == 0)
    return 4;

  if (strcmp(s, "y") == 0)
    return 5;

  if (strcmp(s, "o") == 0)
    return 6;

  if (strcmp(s, "pout") == 0)
    return 2;

  return 0;
}

int easeNo(const char *s)
{
  if (strcmp(s, "stop") == 0)
    return 1;

  if (strcmp(s, "bounce") == 0)
    return 2;

  if (strcmp(s, "linear") == 0)
    return 3;

  if (strcmp(s, "snap") == 0)
    return 4;

  return 0;
}

float easeUygula(int e, float u)
{
  if (e == 1)
    return 1.0f - (1.0f - u) * (1.0f - u);

  if (e == 2)
  {
    if (u < 0.3636f)
      return 7.5625f * u * u;

    if (u < 0.7273f)
    {
      u -= 0.5455f;
      return 7.5625f * u * u + 0.75f;
    }

    if (u < 0.9091f)
    {
      u -= 0.8182f;
      return 7.5625f * u * u + 0.9375f;
    }

    u -= 0.9545f;
    return 7.5625f * u * u + 0.984375f;
  }

  if (e == 3)
    return u;

  if (e == 4)
    return 1.0f;

  return u * u * (3.0f - 2.0f * u);
}

// =====================================================
// JSON KLİP YÜKLEME
// =====================================================

bool klipYukle(const char *json)
{
  JsonDocument doc;

  DeserializationError err = deserializeJson(doc, json);

  if (err)
  {
    Serial.print("JSON okunamadi: ");
    Serial.println(err.c_str());
    return false;
  }

  JsonArray ks = doc["keys"].as<JsonArray>();

  if (ks.isNull())
    return false;

  int yeniKeySayisi = 0;

  for (JsonObject k : ks)
  {
    if (yeniKeySayisi >= MAX_KEY)
      break;

    Anahtar &a = keys[yeniKeySayisi];

    a.t = k["t_ms"] | 0;
    a.ease = easeNo(k["ease"] | "smooth");

    JsonObject f = k["face"];

    Yuz &y = a.yuz;

    y.gozKapali =
        strcmp(f["eye_shape"] | "round", "closed") == 0;

    y.eye_open = f["eye_open"] | 0.9f;
    y.eye_size = f["eye_size"] | 1.0f;
    y.pupil = f["pupil"] | 0.9f;
    y.sparkle = f["sparkle"] | 0.8f;

    y.look_x = f["look_x"] | 0.0f;
    y.look_y = f["look_y"] | 0.0f;

    y.brow_left = f["brow_left"] | 0.0f;
    y.brow_right = f["brow_right"] | 0.0f;
    y.brow_height = f["brow_height"] | 0.0f;

    y.mouth = agizNo(f["mouth"] | "flat");
    y.mouth_open = f["mouth_open"] | 0.0f;

    y.tears = f["tears"] | 0.0f;
    y.blush = f["blush"] | false;
    y.anger_mark = f["anger_mark"] | false;

    a.pose.body_yaw = 0.0f;
    a.pose.head_pan = 0.0f;
    a.pose.head_tilt = 0.0f;
    a.pose.ear_left = 1.0f;
    a.pose.ear_right = 1.0f;

    JsonObject p = k["pose"];

    a.poseVar = !p.isNull();

    if (a.poseVar)
    {
      a.pose.body_yaw = p["body_yaw"] | 0.0f;
      a.pose.head_pan = p["head_pan"] | 0.0f;
      a.pose.head_tilt = p["head_tilt"] | 0.0f;

      a.pose.ear_left = p["ear_left"] | 1.0f;
      a.pose.ear_right = p["ear_right"] | 1.0f;
    }

    yeniKeySayisi++;
  }

  if (yeniKeySayisi == 0)
    return false;

  keySayisi = yeniKeySayisi;

  unsigned long belirtilenSure = doc["duration_ms"] | 0;

  klipSuresi = max(
      belirtilenSure,
      keys[keySayisi - 1].t);

  if (klipSuresi == 0)
  {
    Serial.println("Animasyon suresi sifir olamaz!");
    return false;
  }

  klipDongu = doc["loop"] | false;

  return true;
}

// =====================================================
// YÜZ İNTERPOLASYONU
// =====================================================

Yuz yuzAra(const Yuz &a, const Yuz &b, float u)
{
  Yuz r;

  r.eye_open = ara(a.eye_open, b.eye_open, u);
  r.eye_size = ara(a.eye_size, b.eye_size, u);
  r.pupil = ara(a.pupil, b.pupil, u);
  r.sparkle = ara(a.sparkle, b.sparkle, u);

  r.look_x = ara(a.look_x, b.look_x, u);
  r.look_y = ara(a.look_y, b.look_y, u);

  r.brow_left = ara(a.brow_left, b.brow_left, u);
  r.brow_right = ara(a.brow_right, b.brow_right, u);
  r.brow_height = ara(a.brow_height, b.brow_height, u);

  r.mouth_open = ara(a.mouth_open, b.mouth_open, u);
  r.tears = ara(a.tears, b.tears, u);

  const Yuz &d = (u < 0.5f) ? a : b;

  r.gozKapali = d.gozKapali;
  r.mouth = d.mouth;
  r.blush = d.blush;
  r.anger_mark = d.anger_mark;

  return r;
}

// =====================================================
// SERVO POZ İNTERPOLASYONU
// =====================================================

Poz pozAra(const Poz &a, const Poz &b, float u)
{
  Poz r;

  r.body_yaw = ara(a.body_yaw, b.body_yaw, u);
  r.head_pan = ara(a.head_pan, b.head_pan, u);
  r.head_tilt = ara(a.head_tilt, b.head_tilt, u);

  r.ear_left = ara(a.ear_left, b.ear_left, u);
  r.ear_right = ara(a.ear_right, b.ear_right, u);

  return r;
}

// =====================================================
// SERVO POZUNU UYGULAMA
// =====================================================

void pozServoyaUygula(const Poz &p)
{
  float hedef[NUM_SERVOS];

  hedef[0] = 90.0f + p.body_yaw;
  hedef[1] = 90.0f + p.head_pan;
  hedef[2] = 90.0f + p.head_tilt;

  hedef[3] = 132.0f + (1.0f - p.ear_left) * 18.0f;
  hedef[4] = 48.0f - (1.0f - p.ear_right) * 18.0f;

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    hedef[i] = sinirla(hedef[i], minAci[i], maxAci[i]);

    currentVal[i] = hedef[i];
    servos[i].write((int)roundf(hedef[i]));
  }

  moving = false;
}

// =====================================================
// KAŞ ÇİZİMİ
// =====================================================

void kasCiz(int cx, int y, float aci, int icYon)
{
  float yar = 30;

  float dy = sin(aci * 0.0174533f) * yar;

  int icX = cx + icYon * (int)yar;
  int disX = cx - icYon * (int)yar;

  int icY = y - (int)dy;
  int disY = y + (int)dy;

  for (int t = -2; t <= 2; t++)
  {
    tft.drawLine(
        disX, disY + t,
        icX, icY + t,
        cCizgi);
  }
}

// =====================================================
// AĞIZ ÇİZİMİ
// =====================================================

void agizCiz(int sekil, float acik)
{
  int cx = 160;
  int cy = 190;

  int derinlik = 10 + (int)(40 * acik);

  if (sekil == 1 || sekil == 2)
  {
    for (int x = -50; x <= 50; x++)
    {
      int e = (x * x) * derinlik / 2500;

      int y = (sekil == 1)
                  ? cy + derinlik / 2 - e
                  : cy - derinlik / 2 + e;

      tft.fillCircle(cx + x, y, 2, cCizgi);
    }
  }
  else if (sekil == 3)
  {
    for (int x = -50; x <= 50; x++)
    {
      tft.fillCircle(
          cx + x,
          cy + (int)(8 * sin(x * 0.15f)),
          2,
          cCizgi);
    }
  }
  else if (sekil == 4)
  {
    for (int x = -50; x <= 50; x++)
    {
      int d = (x + 50) % 20;

      tft.fillCircle(
          cx + x,
          cy + abs(d - 10) - 5,
          2,
          cCizgi);
    }
  }
  else if (sekil == 5)
  {
    tft.fillRect(cx - 1, cy - 16, 3, 16, cCizgi);

    for (int x = -30; x <= 30; x++)
    {
      if (x == 0)
        continue;

      int lx = (x < 0) ? x + 15 : x - 15;

      tft.fillCircle(
          cx + x,
          cy + 6 - (lx * lx * 12) / 225,
          2,
          cCizgi);
    }
  }
  else if (sekil == 6)
  {
    int r = 5 + (int)(15 * acik);

    tft.drawCircle(cx, cy, r, cCizgi);
    tft.drawCircle(cx, cy, r - 1, cCizgi);
  }
  else
  {
    tft.fillRect(cx - 40, cy - 2, 80, 5, cCizgi);
  }
}

// =====================================================
// YÜZ ÇİZİMİ
// =====================================================

void yuzCiz(const Yuz &y)
{
  // Yalnızca yüzün bulunduğu alanı temizle.
  tft.fillRect(0, 20, 320, 210, cZemin);

  int gozY = 100;
  int gozX[2] = {100, 220};

  int w = (int)(70 * y.eye_size);
  int h = max(4, (int)(70 * y.eye_size * y.eye_open));

  if (y.blush)
  {
    for (int k = 0; k < 2; k++)
    {
      tft.fillCircle(
          gozX[k],
          gozY + 62,
          14,
          cPembe);
    }
  }

  for (int k = 0; k < 2; k++)
  {
    int cx = gozX[k];

    if (y.gozKapali)
    {
      for (int t = -2; t <= 2; t++)
      {
        tft.drawFastHLine(
            cx - w / 2,
            gozY + t,
            w,
            cCizgi);
      }
    }
    else
    {
      tft.fillRoundRect(
          cx - w / 2,
          gozY - h / 2,
          w,
          h,
          min(w, h) / 2,
          cCizgi);

      int r = (int)(min(w, h) / 2 * 0.5f * y.pupil);

      int dx = max(0, (int)((w / 2 - r) * 0.8f));
      int dy = max(0, h / 2 - r);

      int ix = cx + (int)(y.look_x * dx);
      int iy = gozY + (int)(y.look_y * dy);

      tft.fillCircle(ix, iy, r, cIris);

      if (y.sparkle > 0.3f)
      {
        tft.fillCircle(
            ix - r / 3,
            iy - r / 3,
            max(2, (int)(r * 0.3f * y.sparkle)),
            cBeyaz);
      }
    }
  }

  int kasY = gozY - h / 2 - 14 - (int)(y.brow_height * 40);

  kasCiz(gozX[0], kasY, y.brow_left, 1);
  kasCiz(gozX[1], kasY, y.brow_right, -1);

  agizCiz(y.mouth, y.mouth_open);

  if (y.tears > 0)
  {
    for (int k = 0; k < 2; k++)
    {
      tft.fillCircle(
          gozX[k],
          gozY + h / 2 + 6 + (int)(y.tears * 40),
          5 + (int)(y.tears * 4),
          cGozyasi);
    }
  }

  if (y.anger_mark)
  {
    for (int t = -1; t <= 1; t++)
    {
      tft.drawFastHLine(255, 40 + t, 20, cKirmizi);
      tft.drawFastVLine(265 + t, 30, 20, cKirmizi);
    }
  }
}

// =====================================================
// EKRAN BAŞLATMA
// =====================================================

void ekranBaslat()
{
  SPI.begin(TFT_SCK, TFT_MISO, TFT_MOSI, TFT_CS);

  tft.begin();
  tft.setRotation(1);

  cZemin = tft.color565(0xFB, 0xF8, 0xF3);
  cCizgi = tft.color565(0x2B, 0x2A, 0x33);
  cIris = tft.color565(0x6B, 0x4A, 0x3A);
  cPembe = tft.color565(0xF0, 0x9A, 0xA6);
  cGozyasi = tft.color565(0x5D, 0xAD, 0xE2);
  cBeyaz = tft.color565(255, 255, 255);
  cKirmizi = tft.color565(220, 40, 40);

  tft.fillScreen(cZemin);

  Serial.println("TFT baslatildi!");
}

// =====================================================
// NÖTR YÜZ
// =====================================================

void notrYuzuCiz()
{
  Yuz y = {};

  y.gozKapali = false;

  y.eye_open = 0.9f;
  y.eye_size = 1.0f;
  y.pupil = 0.9f;
  y.sparkle = 0.8f;

  y.look_x = 0.0f;
  y.look_y = 0.0f;

  y.brow_left = 0.0f;
  y.brow_right = 0.0f;
  y.brow_height = 0.0f;

  y.mouth = 0;
  y.mouth_open = 0.0f;

  y.tears = 0.0f;
  y.blush = false;
  y.anger_mark = false;

  yuzCiz(y);
}

// =====================================================
// BAŞLANGIÇ YÜZÜ
// =====================================================

void baslangicYuzuCiz()
{
  notrYuzuCiz();
}

// =====================================================
// KLİP OYNATMA
// =====================================================

bool klipOynat(int no)
{
  if (no < 0 || no >= KLIP_SAYISI)
    return false;

  if (!klipYukle(klipler[no].json))
  {
    oynuyor = false;
    Serial.println("Animasyon yuklenemedi!");
    return false;
  }

  suankiKlip = no;
  klipBaslangic = millis();
  sonCizim = 0;

  oynuyor = true;
  moving = false;

  Serial.print("Animasyon basladi: ");
  Serial.println(klipler[no].ad);

  return true;
}

bool klipAdiylaOynat(const char *ad)
{
  for (int i = 0; i < KLIP_SAYISI; i++)
  {
    if (strcmp(klipler[i].ad, ad) == 0)
    {
      demoModu = false;
      return klipOynat(i);
    }
  }

  return false;
}

// =====================================================
// ANİMASYON GÜNCELLEME
// =====================================================

void klipGuncelle()
{
  if (!oynuyor || keySayisi == 0)
    return;

  unsigned long now = millis();

  if (now - sonCizim < FRAME_INTERVAL)
    return;

  sonCizim = now;

  unsigned long t = now - klipBaslangic;

  if (t >= klipSuresi)
  {
    if (klipDongu)
    {
      t = t % klipSuresi;
      klipBaslangic = now - t;
    }
    else
    {
      // Animasyon tamamlandı.
      // Son karede kalmak yerine doğrudan nötr duruma geç.

      oynuyor = false;
      suankiKlip = -1;

      notrYuzuCiz();
      eda_NotreDon();

      Serial.println("Animasyon bitti. Notr duruma donuldu.");

      return;
    }
  }

  int i = 0;

  while (i < keySayisi - 2 && keys[i + 1].t <= t)
  {
    i++;
  }

  Yuz y;
  Poz p;

  if (t <= keys[0].t)
  {
    y = keys[0].yuz;
    p = keys[0].pose;
  }
  else if (i >= keySayisi - 1)
  {
    y = keys[keySayisi - 1].yuz;
    p = keys[keySayisi - 1].pose;
  }
  else
  {
    unsigned long fark = keys[i + 1].t - keys[i].t;

    float u = (fark == 0)
                  ? 1.0f
                  : (float)(t - keys[i].t) / fark;

    u = easeUygula(keys[i + 1].ease, u);

    y = yuzAra(keys[i].yuz, keys[i + 1].yuz, u);

    if (keys[i].poseVar && keys[i + 1].poseVar)
    {
      p = pozAra(keys[i].pose, keys[i + 1].pose, u);
    }
    else if (keys[i + 1].poseVar)
    {
      p = keys[i + 1].pose;
    }
    else
    {
      p = keys[i].pose;
    }
  }

  yuzCiz(y);
  pozServoyaUygula(p);
}

// =====================================================
// SERİ CEVAPLARI
// =====================================================

void ackGonder(int seq)
{
  JsonDocument doc;

  doc["ack"] = seq;
  doc["ok"] = true;

  serializeJson(doc, Serial);
  Serial.println();
}

void hataGonder(int seq, const char *kod)
{
  JsonDocument doc;

  doc["ack"] = seq;
  doc["ok"] = false;
  doc["err"] = kod;

  serializeJson(doc, Serial);
  Serial.println();
}

// =====================================================
// SERİ KOMUTLARINI İŞLEME
// =====================================================

void mesajIsle(char *satir)
{
  JsonDocument doc;

  DeserializationError error = deserializeJson(doc, satir);

  if (error)
  {
    hataGonder(-1, "bad_json");
    return;
  }

  int seq = doc["seq"] | -1;
  const char *cmd = doc["cmd"];

  if (cmd == nullptr)
  {
    hataGonder(seq, "bad_cmd");
    return;
  }

  // PING
  if (strcmp(cmd, "ping") == 0)
  {
    if (!oynuyor)
    {
      sonMesajZamani = millis();
      sigortaDevredeMi = true;
    }

    ackGonder(seq);
  }

  // NEUTRAL
  else if (strcmp(cmd, "neutral") == 0)
  {
    oynuyor = false;
    suankiKlip = -1;

    sonMesajZamani = millis();
    sigortaDevredeMi = true;

    notrYuzuCiz();
    eda_NotreDon();

    ackGonder(seq);
  }

  // MOVE
  else if (strcmp(cmd, "move") == 0)
  {
    if (!doc.containsKey("deg") || !doc.containsKey("ms"))
    {
      hataGonder(seq, "bad_cmd");
      return;
    }

    JsonArray deg = doc["deg"].as<JsonArray>();
    int ms = doc["ms"] | -1;

    if (deg.isNull() || deg.size() != 5 || ms < 0)
    {
      hataGonder(seq, "out_of_range");
      return;
    }

    int acilar[5];

    for (int i = 0; i < 5; i++)
    {
      if (!deg[i].is<int>())
      {
        hataGonder(seq, "out_of_range");
        return;
      }

      acilar[i] = deg[i].as<int>();

      if (acilar[i] < minAci[i] || acilar[i] > maxAci[i])
      {
        hataGonder(seq, "out_of_range");
        return;
      }
    }

    oynuyor = false;
    suankiKlip = -1;

    eda_HedefeGit(acilar, ms);

    sonMesajZamani = millis();
    sigortaDevredeMi = true;

    ackGonder(seq);
  }

  // ANIM
  else if (strcmp(cmd, "anim") == 0)
  {
    const char *ad = doc["name"];

    if (ad == nullptr || !klipAdiylaOynat(ad))
    {
      hataGonder(seq, "bad_cmd");
      return;
    }

    sigortaDevredeMi = false;

    ackGonder(seq);
  }

  // PLAY VE EMOTION
  else if (
      strcmp(cmd, "play") == 0 ||
      strcmp(cmd, "emotion") == 0)
  {
    const char *ad = doc["name"];

    if (ad == nullptr)
      ad = doc["emotion"];

    if (ad == nullptr || !klipAdiylaOynat(ad))
    {
      hataGonder(seq, "bad_cmd");
      return;
    }

    sigortaDevredeMi = false;

    ackGonder(seq);
  }

  // TANIMSIZ KOMUT
  else
  {
    hataGonder(seq, "bad_cmd");
  }
}

// =====================================================
// SERİ OKUMA
// JSON TAMAMLANINCA SATIR SONU BEKLEMEDEN İŞLE
// =====================================================

void seriOku()
{
  static int parantezDerinligi = 0;
  static bool metinIcinde = false;
  static bool oncekiTersSlash = false;

  while (Serial.available() > 0)
  {
    char c = Serial.read();

    if (serialIndex == 0)
    {
      if (c != '{')
        continue;

      parantezDerinligi = 0;
      metinIcinde = false;
      oncekiTersSlash = false;
    }

    if (serialIndex >= (int)sizeof(serialBuffer) - 1)
    {
      serialIndex = 0;
      parantezDerinligi = 0;
      metinIcinde = false;
      oncekiTersSlash = false;

      hataGonder(-1, "buffer_overflow");
      continue;
    }

    serialBuffer[serialIndex++] = c;

    if (metinIcinde)
    {
      if (oncekiTersSlash)
      {
        oncekiTersSlash = false;
      }
      else if (c == '\\')
      {
        oncekiTersSlash = true;
      }
      else if (c == '"')
      {
        metinIcinde = false;
      }
    }
    else
    {
      if (c == '"')
      {
        metinIcinde = true;
      }
      else if (c == '{')
      {
        parantezDerinligi++;
      }
      else if (c == '}')
      {
        parantezDerinligi--;
      }
    }

    if (parantezDerinligi == 0 &&
        !metinIcinde &&
        serialIndex > 0)
    {
      serialBuffer[serialIndex] = '\0';

      mesajIsle(serialBuffer);

      serialIndex = 0;
      parantezDerinligi = 0;
      metinIcinde = false;
      oncekiTersSlash = false;
    }
  }
}

// =====================================================
// SETUP
// =====================================================

void setup()
{
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("PET ROBOT BASLATILIYOR...");

  eda_Baslat();

  ekranBaslat();

  baslangicYuzuCiz();

  Serial.println("PET ROBOT BASLATILDI!");
  Serial.println("JSON KOMUTU BEKLENIYOR...");
}

// =====================================================
// LOOP
// =====================================================

void loop()
{
  seriOku();

  if (oynuyor)
  {
    klipGuncelle();
  }
  else
  {
    servoGuncelle();
  }

  // Güvenlik zaman aşımı.
  if (sigortaDevredeMi &&
      millis() - sonMesajZamani > SIGORTA_SURESI)
  {
    sigortaDevredeMi = false;
    oynuyor = false;
    suankiKlip = -1;

    notrYuzuCiz();
    eda_NotreDon();

    Serial.println("SIGORTA: Notr duruma donuluyor.");
  }
}
