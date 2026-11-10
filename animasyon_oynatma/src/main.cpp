
#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include "animasyonlar.h"

// Test için 1 yap: seri monitöre fps yazar (gerçek bağlantıda 0 kalsın,
// yoksa Onur'un JSON okumasını bozar)
#define FPS_YAZ 0

// Ekran SPI hızı: 40 MHz
const uint32_t SPI_HIZ = 40000000;

// --- GÜVENLİK VE İLETİŞİM DEĞİŞKENLERİ ---
unsigned long sonMesajZamani = 0;
bool sigortaDevredeMi = false;
String gelenSatir = "";

// --- SERVO VE HAREKET DEĞİŞKENLERİ ---
const int NUM_SERVOS = 5;
const int pins[NUM_SERVOS] = {13, 12, 14, 27, 26};

// Servonun gidebileceği fiziksel açı sınırları
const int minAci[NUM_SERVOS] = {45, 0, 80, 60, 30};
const int maxAci[NUM_SERVOS] = {135, 180, 135, 150, 120};

// Başlangıç/Nötr açıları
const int idleAci[NUM_SERVOS] = {90, 90, 90, 132, 48};

const unsigned long IDLE_RETURN_MS = 800;
const unsigned long UPDATE_INTERVAL = 10;

// Klip değişirken yüz ve servoların eski halden yeni hale geçiş süresi
const unsigned long GECIS_MS = 250;

Servo servos[NUM_SERVOS];
float startVal[NUM_SERVOS];
float targetVal[NUM_SERVOS];
float currentVal[NUM_SERVOS];

unsigned long moveStart = 0;
unsigned long moveDuration = 0;
bool moving = false;
unsigned long lastUpdate = 0;

// JSON servo animasyonu aktif mi?
bool poseAnimasyonuAktif = false;
unsigned long sonPoseGuncelleme = 0;

// Klip geçişi için: klip başlarken servoların o anki açıları
float gecisAcilar[NUM_SERVOS];
unsigned long gecisZamani = 0;

// Son yazılan servo mikrosaniyesi (aynı değeri tekrar yazmamak için)
int sonUs[NUM_SERVOS];

// --- EKRAN DEĞİŞKENLERİ ---
#define TFT_CS 5
#define TFT_DC 2
#define TFT_RST 4

Adafruit_ILI9341 tft(TFT_CS, TFT_DC, TFT_RST);

const int EKRAN_W = 320;
const int EKRAN_H = 240;
const int SERIT_H = 60;

GFXcanvas16 canvas(EKRAN_W, SERIT_H);
int seritY = 0;

// Her şeridin ekrana en son gönderilen içeriğinin özeti
uint32_t seritOzet[EKRAN_H / SERIT_H];

// fps ölçümü için sayaçlar
unsigned long fpsSay = 0;
unsigned long seritGonderilen = 0;
unsigned long fpsZaman = 0;

// Renkler
uint16_t cZemin, cCizgi, cIris, cPembe, cGozyasi, cBeyaz, cKirmizi;

// --- KLİP DEĞİŞKENLERİ ---
const int MAX_KEY = 24;
Anahtar keys[MAX_KEY];

int keySayisi = 0;
unsigned long klipSuresi = 1;
unsigned long klipBaslangic = 0;
unsigned long sonKareZamani = 0;

const unsigned long KARE_ARALIGI = 33;

bool kareCiziliyor = false;

int idleKlipNo = -1;
bool idleOynuyor = false;

// --- ÇİZİM İÇİN YUMUŞAK YÜZ DURUMU ---
const int AGIZ_SEKIL = 6;
const int AGIZ_N = 101;

struct YuzR
{
  float kapali;
  float eye_open, eye_size, pupil, sparkle;
  float look_x, look_y;
  float brow_left, brow_right, brow_height;
  float mouth_open, tears;
  float blush, anger;
  float mw[AGIZ_SEKIL];
};

YuzR kareR;
YuzR gecisR;
bool ilkYukleme = true;

float agizYv[AGIZ_N];
float agizHW = 0;

const float agizYari[AGIZ_SEKIL] = {40, 50, 50, 50, 50, 30};

// =========================================================================
// HAREKET VE MOTOR FONKSİYONLARI
// =========================================================================

void servoYaz(int i, float aci)
{
  int us = 500 + (int)(aci * (2400 - 500) / 180.0f);

  if (us == sonUs[i])
    return;

  sonUs[i] = us;
  servos[i].writeMicroseconds(us);
}

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

void motorlariBaslat()
{
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    servos[i].attach(pins[i], 500, 2400);

    currentVal[i] = idleAci[i];
    startVal[i] = idleAci[i];
    targetVal[i] = idleAci[i];

    servoYaz(i, idleAci[i]);
  }
}

void servoGuncelle()
{
  if (!moving)
    return;

  unsigned long now = millis();

  if (now - lastUpdate < UPDATE_INTERVAL)
    return;

  lastUpdate = now;

  float t = (moveDuration == 0)
                ? 1.0f
                : (float)(now - moveStart) / moveDuration;

  if (t >= 1.0f)
  {
    t = 1.0f;
    moving = false;
  }

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    currentVal[i] = startVal[i] +
                    (targetVal[i] - startVal[i]) * t;

    servoYaz(i, currentVal[i]);
  }
}

void hedefAcilaraGit(int hedefAcilar[5], int sure_ms)
{
  float target[NUM_SERVOS];

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    target[i] = constrain(
        hedefAcilar[i],
        minAci[i],
        maxAci[i]);
  }

  hareketBaslat(target, sure_ms);
}

void notrPozisyonaDon()
{
  float target[NUM_SERVOS];

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    target[i] = idleAci[i];
  }

  hareketBaslat(target, IDLE_RETURN_MS);
}

// =========================================================================
// EKRAN VE YÜZ ANİMASYONU FONKSİYONLARI
// =========================================================================

void daireCiz(int x, int y, int r, uint16_t renk)
{
  canvas.fillCircle(x, y - seritY, r, renk);
}

void cizgiCiz(int x0, int y0, int x1, int y1, uint16_t renk)
{
  canvas.drawLine(x0, y0 - seritY, x1, y1 - seritY, renk);
}

void kutuCiz(int x, int y, int w, int h, uint16_t renk)
{
  canvas.fillRect(x, y - seritY, w, h, renk);
}

void yuvarlakKutuCiz(int x, int y, int w, int h, int r, uint16_t renk)
{
  canvas.fillRoundRect(x, y - seritY, w, h, r, renk);
}

void yatayCiz(int x, int y, int w, uint16_t renk)
{
  canvas.drawFastHLine(x, y - seritY, w, renk);
}

void dikeyCiz(int x, int y, int h, uint16_t renk)
{
  canvas.drawFastVLine(x, y - seritY, h, renk);
}

uint16_t karistir(uint16_t a, uint16_t b, float t)
{
  t = constrain(t, 0.0f, 1.0f);

  int ar = (a >> 11) & 31;
  int ag = (a >> 5) & 63;
  int ab = a & 31;

  int br = (b >> 11) & 31;
  int bg = (b >> 5) & 63;
  int bb = b & 31;

  int r = ar + (int)((br - ar) * t);
  int g = ag + (int)((bg - ag) * t);
  int bl = ab + (int)((bb - ab) * t);

  return (r << 11) | (g << 5) | bl;
}

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

// =========================================================================
// JSON KLİP YÜKLEME
// =========================================================================

bool klipYukle(const char *json)
{
  JsonDocument doc;

  DeserializationError err = deserializeJson(doc, json);

  if (err)
    return false;

  int n = 0;

  JsonArray ks = doc["keys"].as<JsonArray>();

  for (JsonObject k : ks)
  {
    if (n >= MAX_KEY)
      break;

    Anahtar &a = keys[n];

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

    JsonObject p = k["pose"].as<JsonObject>();

    a.poseVar = !p.isNull();

    a.pose.body_yaw = p["body_yaw"] | 0.0f;
    a.pose.head_pan = p["head_pan"] | 0.0f;
    a.pose.head_tilt = p["head_tilt"] | 0.0f;

    a.pose.ear_left = p["ear_left"] | 1.0f;
    a.pose.ear_right = p["ear_right"] | 1.0f;

    n++;
  }

  if (n == 0)
    return false;

  keySayisi = n;

  unsigned long sure = doc["duration_ms"] | 0;

  klipSuresi =
      (sure > keys[n - 1].t)
          ? sure
          : keys[n - 1].t;

  if (klipSuresi == 0)
    klipSuresi = 1;

  return true;
}

// =========================================================================
// ANİMASYON HESAPLAMALARI
// =========================================================================

float ara(float a, float b, float u)
{
  return a + (b - a) * u;
}

float easeUygula(int e, float u)
{
  if (e == 1)
    return 1 - (1 - u) * (1 - u);

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
    return 1;

  return u * u * (3 - 2 * u);
}

// =========================================================================
// YÜZ ARA DEĞER HESAPLAMASI
// =========================================================================

YuzR yuzdenR(const Yuz &y)
{
  YuzR r;

  r.kapali = y.gozKapali ? 1.0f : 0.0f;

  r.eye_open = y.eye_open;
  r.eye_size = y.eye_size;
  r.pupil = y.pupil;
  r.sparkle = y.sparkle;

  r.look_x = y.look_x;
  r.look_y = y.look_y;

  r.brow_left = y.brow_left;
  r.brow_right = y.brow_right;
  r.brow_height = y.brow_height;

  r.mouth_open = y.mouth_open;
  r.tears = y.tears;

  r.blush = y.blush ? 1.0f : 0.0f;
  r.anger = y.anger_mark ? 1.0f : 0.0f;

  for (int k = 0; k < AGIZ_SEKIL; k++)
    r.mw[k] = 0;

  int m = y.mouth;

  if (m < 0 || m >= AGIZ_SEKIL)
    m = 0;

  r.mw[m] = 1.0f;

  return r;
}

YuzR yuzRAra(const YuzR &a, const YuzR &b, float u)
{
  YuzR r;

  r.kapali = ara(a.kapali, b.kapali, u);

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

  r.blush = ara(a.blush, b.blush, u);
  r.anger = ara(a.anger, b.anger, u);

  for (int k = 0; k < AGIZ_SEKIL; k++)
    r.mw[k] = ara(a.mw[k], b.mw[k], u);

  return r;
}

// =========================================================================
// AĞIZ ŞEKİLLERİ
// =========================================================================

float agizYuksekligi(int sekil, float x, int derinlik)
{
  if (sekil == 1)
    return derinlik / 2.0f - (x * x) * derinlik / 2500.0f;

  if (sekil == 2)
    return -derinlik / 2.0f + (x * x) * derinlik / 2500.0f;

  if (sekil == 3)
    return 8 * sinf(x * 0.15f);

  if (sekil == 4)
  {
    float d = fmodf(x + 50, 20);
    return fabsf(d - 10) - 5;
  }

  if (sekil == 5)
  {
    float lx = (x < 0) ? x + 15 : x - 15;
    return 6 - (lx * lx * 12) / 225.0f;
  }

  return 0;
}

void agizHazirla()
{
  float hw = 0;

  for (int k = 0; k < AGIZ_SEKIL; k++)
    hw += kareR.mw[k] * agizYari[k];

  agizHW = hw;

  int derinlik =
      10 + (int)(40 * constrain(kareR.mouth_open, 0.0f, 1.2f));

  for (int j = 0; j < AGIZ_N; j++)
  {
    float xn = (j - AGIZ_N / 2) / (float)(AGIZ_N / 2);

    float y = 0;

    for (int k = 0; k < AGIZ_SEKIL; k++)
    {
      if (kareR.mw[k] > 0.001f)
      {
        y += kareR.mw[k] *
             agizYuksekligi(k, xn * agizYari[k], derinlik);
      }
    }

    agizYv[j] = y;
  }
}

// =========================================================================
// SERVO ARA DEĞER HESAPLAMASI
// =========================================================================

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

// =========================================================================
// JSON SERVO ANİMASYONU
// =========================================================================

void servoPoseGuncelle()
{
  if (!poseAnimasyonuAktif || keySayisi == 0)
    return;

  unsigned long now = millis();

  if (now - sonPoseGuncelleme < UPDATE_INTERVAL)
    return;

  sonPoseGuncelleme = now;

  unsigned long t = now - klipBaslangic;

  if (idleOynuyor && klipSuresi > 0)
  {
    t %= klipSuresi;
  }

  Poz p;

  if (t <= keys[0].t)
  {
    p = keys[0].pose;
  }
  else if (t >= keys[keySayisi - 1].t)
  {
    p = keys[keySayisi - 1].pose;
  }
  else
  {
    int i = 0;

    while (i < keySayisi - 2 && keys[i + 1].t <= t)
    {
      i++;
    }

    unsigned long fark =
        keys[i + 1].t - keys[i].t;

    float u = (fark == 0)
                  ? 1.0f
                  : (float)(t - keys[i].t) / fark;

    u = easeUygula(keys[i + 1].ease, u);

    p = pozAra(
        keys[i].pose,
        keys[i + 1].pose,
        u);
  }

  float acilar[NUM_SERVOS];

  acilar[0] = 90.0f + p.body_yaw;
  acilar[1] = 90.0f + p.head_pan;
  acilar[2] = 90.0f + p.head_tilt;

  // Kulaklar: 0 = nötr, 1 = tam açık
  acilar[3] =
      idleAci[3] +
      p.ear_left * (maxAci[3] - idleAci[3]);

  acilar[4] =
      idleAci[4] -
      p.ear_right * (idleAci[4] - minAci[4]);

  float w = 1.0f;
  unsigned long g = now - gecisZamani;

  if (g < GECIS_MS)
  {
    w = (float)g / GECIS_MS;
    w = w * w * (3 - 2 * w);
  }

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    float a = constrain(
        acilar[i],
        (float)minAci[i],
        (float)maxAci[i]);

    if (w < 1.0f)
      a = gecisAcilar[i] + (a - gecisAcilar[i]) * w;

    currentVal[i] = a;

    servoYaz(i, a);
  }

  moving = false;
}

// =========================================================================
// YÜZ ÇİZİM FONKSİYONLARI
// =========================================================================

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
    cizgiCiz(
        disX,
        disY + t,
        icX,
        icY + t,
        cCizgi);
  }
}

void agizCiz()
{
  int cx = 160;
  int cy = 190;

  for (int j = 0; j < AGIZ_N; j++)
  {
    float xn = (j - AGIZ_N / 2) / (float)(AGIZ_N / 2);

    daireCiz(
        cx + (int)roundf(xn * agizHW),
        cy + (int)roundf(agizYv[j]),
        2,
        cCizgi);
  }

  int bh = (int)(16 * kareR.mw[5]);

  if (bh > 0)
    kutuCiz(cx - 1, cy - bh, 3, bh, cCizgi);
}

void yuzCiz(const YuzR &y)
{
  int gozY = 100;

  int gozX[2] = {100, 220};

  int w = (int)(70 * y.eye_size);

  int h = max(
      5,
      (int)(70 * y.eye_size * y.eye_open * (1.0f - y.kapali)));

  int hKas = max(
      5,
      (int)(70 * y.eye_size * y.eye_open));

  if (y.blush > 0.02f)
  {
    uint16_t cYanak = karistir(cZemin, cPembe, y.blush);

    for (int k = 0; k < 2; k++)
    {
      daireCiz(
          gozX[k],
          gozY + 62,
          14,
          cYanak);
    }
  }

  for (int k = 0; k < 2; k++)
  {
    int cx = gozX[k];

    yuvarlakKutuCiz(
        cx - w / 2,
        gozY - h / 2,
        w,
        h,
        min(w, h) / 2,
        cCizgi);

    int r = (int)(min(w, h) / 2 * 0.5f * y.pupil);

    float acikOran = constrain((h - 8) / 16.0f, 0.0f, 1.0f);
    r = (int)(r * acikOran);

    if (r >= 2)
    {
      int dx = max(
          0,
          (int)((w / 2 - r) * 0.8f));

      int dy = max(
          0,
          h / 2 - r);

      int ix = cx + (int)(y.look_x * dx);
      int iy = gozY + (int)(y.look_y * dy);

      daireCiz(ix, iy, r, cIris);

      if (y.sparkle > 0.3f)
      {
        daireCiz(
            ix - r / 3,
            iy - r / 3,
            max(2, (int)(r * 0.3f * y.sparkle)),
            cBeyaz);
      }
    }
  }

  int kasY =
      gozY - hKas / 2 - 14 - (int)(y.brow_height * 40);

  kasCiz(gozX[0], kasY, y.brow_left, 1);
  kasCiz(gozX[1], kasY, y.brow_right, -1);

  agizCiz();

  if (y.tears > 0)
  {
    for (int k = 0; k < 2; k++)
    {
      daireCiz(
          gozX[k],
          gozY + hKas / 2 + 6 + (int)(y.tears * 40),
          5 + (int)(y.tears * 4),
          cGozyasi);
    }
  }

  if (y.anger > 0.02f)
  {
    uint16_t cOfke = karistir(cZemin, cKirmizi, y.anger);

    for (int t = -1; t <= 1; t++)
    {
      yatayCiz(255, 40 + t, 20, cOfke);
      dikeyCiz(265 + t, 30, 20, cOfke);
    }
  }
}

// =========================================================================
// KLİP OYNATMA FONKSİYONLARI
// =========================================================================

bool klipOynat(int no, bool poseOynasin = true)
{
  if (!klipYukle(klipler[no].json))
    return false;

  if (ilkYukleme)
  {
    kareR = yuzdenR(keys[0].yuz);
    ilkYukleme = false;
  }

  gecisR = kareR;

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    gecisAcilar[i] = currentVal[i];
  }

  gecisZamani = millis();

  klipBaslangic = millis();

  idleOynuyor = (no == idleKlipNo);

  kareCiziliyor = false;
  sonKareZamani = 0;

  poseAnimasyonuAktif = poseOynasin;
  sonPoseGuncelleme = 0;

  if (poseOynasin)
    moving = false;

  return true;
}

bool klipAdiylaOynat(const char *ad)
{
  for (int i = 0; i < KLIP_SAYISI; i++)
  {
    if (strcmp(klipler[i].ad, ad) == 0)
    {
      return klipOynat(i);
    }
  }

  return false;
}

// =========================================================================
// YENİ KARE HAZIRLAMA
// =========================================================================

void kareHazirla()
{
  unsigned long now = millis();

  unsigned long t = now - klipBaslangic;

  if (t >= klipSuresi)
  {
    if (idleOynuyor || idleKlipNo < 0)
    {
      t = t % klipSuresi;

      klipBaslangic = now - t;
    }
    else
    {
      klipOynat(idleKlipNo);
      return;
    }
  }

  YuzR hedef;

  if (t <= keys[0].t)
  {
    hedef = yuzdenR(keys[0].yuz);
  }
  else if (t >= keys[keySayisi - 1].t)
  {
    hedef = yuzdenR(keys[keySayisi - 1].yuz);
  }
  else
  {
    int i = 0;

    while (i < keySayisi - 2 && keys[i + 1].t <= t)
    {
      i++;
    }

    unsigned long fark =
        keys[i + 1].t - keys[i].t;

    float u =
        (fark == 0)
            ? 1.0f
            : (float)(t - keys[i].t) / fark;

    hedef = yuzRAra(
        yuzdenR(keys[i].yuz),
        yuzdenR(keys[i + 1].yuz),
        easeUygula(keys[i + 1].ease, u));
  }

  unsigned long g = now - gecisZamani;

  if (g < GECIS_MS)
  {
    float w = (float)g / GECIS_MS;
    w = w * w * (3 - 2 * w);

    kareR = yuzRAra(gecisR, hedef, w);
  }
  else
  {
    kareR = hedef;
  }

  agizHazirla();

  seritY = 0;

  kareCiziliyor = true;
}

// =========================================================================
// EKRANA ŞERİT ÇİZME
// =========================================================================

uint32_t canvasOzet()
{
  const uint32_t *p = (const uint32_t *)canvas.getBuffer();

  uint32_t h = 2166136261u;

  for (int i = 0; i < EKRAN_W * SERIT_H / 2; i++)
  {
    h = (h ^ p[i]) * 16777619u;
  }

  return h;
}

void seritCiz()
{
  canvas.fillScreen(cZemin);

  yuzCiz(kareR);

  int no = seritY / SERIT_H;
  uint32_t ozet = canvasOzet();

  if (ozet != seritOzet[no])
  {
    seritOzet[no] = ozet;

    tft.drawRGBBitmap(
        0,
        seritY,
        canvas.getBuffer(),
        EKRAN_W,
        SERIT_H);

    seritGonderilen++;
  }

  seritY += SERIT_H;

  if (seritY >= EKRAN_H)
  {
    kareCiziliyor = false;
    fpsSay++;
  }
}

// =========================================================================
// EKRAN ANİMASYONU GÜNCELLEME
// =========================================================================

void klipGuncelle()
{
  if (!kareCiziliyor)
  {
    if (millis() - sonKareZamani < KARE_ARALIGI)
      return;

    sonKareZamani = millis();

    kareHazirla();

    return;
  }

  seritCiz();
}

// =========================================================================
// EKRAN BAŞLATMA
// =========================================================================

void ekranBaslat()
{
  tft.begin(SPI_HIZ);

  tft.setRotation(1);

  cZemin = tft.color565(0xFB, 0xF8, 0xF3);
  cCizgi = tft.color565(0x2B, 0x2A, 0x33);
  cIris = tft.color565(0x6B, 0x4A, 0x3A);
  cPembe = tft.color565(0xF0, 0x9A, 0xA6);
  cGozyasi = tft.color565(0x5D, 0xAD, 0xE2);
  cBeyaz = tft.color565(255, 255, 255);
  cKirmizi = tft.color565(220, 40, 40);

  tft.fillScreen(cZemin);

  for (int i = 0; i < KLIP_SAYISI; i++)
  {
    if (strcmp(klipler[i].ad, "idle") == 0)
    {
      idleKlipNo = i;
    }
  }

  if (idleKlipNo >= 0)
  {
    klipOynat(idleKlipNo);
  }
}

// =========================================================================
// İLETİŞİM FONKSİYONLARI
// =========================================================================

void ackGonder(int seqNumarasi)
{
  StaticJsonDocument<64> doc;

  doc["ack"] = seqNumarasi;
  doc["ok"] = true;

  serializeJson(doc, Serial);

  Serial.println();
}

void hataGonder(int seqNumarasi, const char *hataKodu)
{
  StaticJsonDocument<96> doc;

  doc["ack"] = seqNumarasi;
  doc["ok"] = false;
  doc["err"] = hataKodu;

  serializeJson(doc, Serial);

  Serial.println();
}

// =========================================================================
// SETUP
// =========================================================================

void setup()
{
  Serial.begin(115200);

  sonMesajZamani = millis();

  motorlariBaslat();

  ekranBaslat();
}

// =========================================================================
// LOOP
// =========================================================================

void loop()
{
  servoGuncelle();

  servoPoseGuncelle();

  klipGuncelle();

  // Seri porttan mesaj oku:
  // JSON } karakterinde veya satır sonunda tamamlanır.
  while (Serial.available() > 0)
  {
    char c = Serial.read();

    bool mesajHazir = false;

    if (c == '}')
    {
      gelenSatir += c;
      mesajHazir = true;
    }
    else if (c == '\n' || c == '\r')
    {
      mesajHazir = true;
    }
    else
    {
      gelenSatir += c;
    }

    if (mesajHazir)
    {
      gelenSatir.trim();

      if (gelenSatir.length() > 0)
      {
        StaticJsonDocument<256> doc;

        DeserializationError error =
            deserializeJson(doc, gelenSatir);

        if (error)
        {
          hataGonder(-1, "bad_json");
        }
        else
        {
          int seq = doc["seq"] | -1;

          const char *cmd = doc["cmd"];

          if (cmd == nullptr)
          {
            hataGonder(seq, "bad_cmd");
          }

          else if (strcmp(cmd, "ping") == 0)
          {
            sonMesajZamani = millis();

            sigortaDevredeMi = true;

            ackGonder(seq);
          }

          else if (strcmp(cmd, "neutral") == 0)
          {
            sonMesajZamani = millis();

            sigortaDevredeMi = true;

            if (idleKlipNo >= 0)
            {
              klipOynat(idleKlipNo, false);
            }

            poseAnimasyonuAktif = false;

            notrPozisyonaDon();

            ackGonder(seq);
          }

          else if (strcmp(cmd, "move") == 0)
          {
            if (!doc.containsKey("deg") ||
                !doc.containsKey("ms"))
            {
              hataGonder(seq, "bad_cmd");
            }
            else
            {
              JsonArray degArray =
                  doc["deg"].as<JsonArray>();

              int ms = doc["ms"];

              if (degArray.size() != 5 || ms < 0)
              {
                hataGonder(seq, "out_of_range");
              }
              else
              {
                int acilar[5];

                bool sinirDisi = false;

                for (int i = 0; i < 5; i++)
                {
                  acilar[i] = degArray[i];

                  if (acilar[i] < minAci[i] ||
                      acilar[i] > maxAci[i])
                  {
                    sinirDisi = true;
                  }
                }

                if (sinirDisi)
                {
                  hataGonder(seq, "out_of_range");
                }
                else
                {
                  sonMesajZamani = millis();

                  sigortaDevredeMi = true;

                  poseAnimasyonuAktif = false;

                  hedefAcilaraGit(acilar, ms);

                  ackGonder(seq);
                }
              }
            }
          }

          else if (strcmp(cmd, "anim") == 0)
          {
            const char *ad = doc["name"];

            if (ad == nullptr || !klipAdiylaOynat(ad))
            {
              hataGonder(seq, "bad_cmd");
            }
            else
            {
              sonMesajZamani = millis();

              sigortaDevredeMi = true;

              ackGonder(seq);
            }
          }

          else
          {
            hataGonder(seq, "bad_cmd");
          }
        }
      }

      gelenSatir = "";
    }
  }

#if FPS_YAZ
  if (millis() - fpsZaman >= 2000)
  {
    Serial.printf(
        "\nfps: %.1f, gonderilen serit: %lu / %lu\n",
        fpsSay / 2.0f,
        seritGonderilen,
        fpsSay * (EKRAN_H / SERIT_H));

    fpsSay = 0;
    seritGonderilen = 0;
    fpsZaman = millis();
  }
#endif

  // 3 saniye boyunca ping gelmezse nötre dön
  if (sigortaDevredeMi &&
      (millis() - sonMesajZamani > 3000))
  {
    poseAnimasyonuAktif = false;

    notrPozisyonaDon();

    sigortaDevredeMi = false;
  }
}
